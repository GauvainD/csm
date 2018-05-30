import json

import os

from csm.input_output.formatters import format_CSM, non_negative_zero, format_perm_count
import io
from openbabel import OBConversion
from csm.calculations.basic_calculations import check_perm_structure_preservation, check_perm_cycles, cart2sph
from csm.molecule.molecule import MoleculeReader, get_format, mol_string_from_obm
from csm.input_output.formatters import csm_log as print

from csv import DictWriter

def write_array_to_file(f, arr, add_one=False, separator=" "):
    '''
    :param f: filestream being written to
    :param arr: array being written
    :param add_one: some arrays should be written with 1-index instead of 0 index, if so add_one=True
    :param separator: default is " "
    '''
    for item in arr:
        if add_one:
            item = item + 1
        f.write(str(item) + separator)


# molwriters
class CSMMolWriter:
    def write(self, f, result, op_name, format="csm"):
        self.print_output_csm(f, result, op_name)

    def print_output_csm(self, f, result, op_name):
        """
        Prints output in CSM format
        :param f: File to print to
        :param result: The result of the CSM calculation (a CSMState)
        :param calc_args: Calculation arguments to CSM
        """
        size = len(result.molecule.atoms)

        # print initial molecule

        f.write("\nINITIAL STRUCTURE COORDINATES\n%i\n\n" % size)
        for i in range(size):
            f.write("%3s%10.5lf %10.5lf %10.5lf\n" %
                    (result.molecule.atoms[i].symbol,
                     non_negative_zero(result.molecule.atoms[i].pos[0]),
                     non_negative_zero(result.molecule.atoms[i].pos[1]),
                     non_negative_zero(result.molecule.atoms[i].pos[2])))

        for i in range(size):
            f.write("%d " % (i + 1))
            for j in result.molecule.atoms[i].adjacent:
                f.write("%d " % (j + 1))
            f.write("\n")

        # print resulting structure coordinates

        f.write("\nMODEL 02 RESULTING STRUCTURE COORDINATES\n%i\n" % size)

        for i in range(size):
            f.write("%3s%10.5lf %10.5lf %10.5lf\n" %
                    (result.molecule.atoms[i].symbol,
                     non_negative_zero(result.symmetric_structure[i][0]),
                     non_negative_zero(result.symmetric_structure[i][1]),
                     non_negative_zero(result.symmetric_structure[i][2])))

        for i in range(size):
            f.write("%d " % (i + 1))
            for j in result.molecule.atoms[i].adjacent:
                f.write("%d " % (j + 1))
            f.write("\n")


def write_ob_molecule(obmol, format, f, legacy=False):
        """
        Write an Open Babel molecule to file
        :param obmol: The molecule
        :param format: The output format
        :param f: The file to write output to
        :param f_name: The file's name (for extension-finding purpose)
        """
        conv = OBConversion()
        if not conv.SetOutFormat(format):
            raise ValueError("Error setting output format to " + format)

        # write to file

        try:
            s = conv.WriteString(obmol)
        except (TypeError, ValueError, IOError):
            raise ValueError("Error writing data file using OpenBabel")

        if legacy:
            if str.lower(format) == 'pdb':
                s = s.replace("END", "ENDMDL")
        f.write(s)


class OBMolWriter:
    def write(self, f, result, op_name, format):
        self.legacy_print_output_ob(f, result, format, op_name)

    def legacy_print_output_ob(self, f, result, format, op_name):
        """
        Prints output using Open Babel
        :param f: File to write to
        :param result: The result of the CSM calculation (a CSMState)
        :param in_args: Input arguments to CSM
        :param calc_args: Calculation arguments to CSM
        :param out_args: Output arguments to CSM
        """
        # print initial molecule
        if format == 'pdb':
            f.write("\nMODEL 01")
        f.write("\nINITIAL STRUCTURE COORDINATES\n")

        obmols=self.obm_from_result(result)
        obmol=obmols[0]
        self.set_obm_from_original(obmol, result)
        write_ob_molecule(obmol, format, f, legacy=True)

        if format == 'pdb':
            f.write("\nMODEL 02")
        f.write("\nRESULTING STRUCTURE COORDINATES\n")

        self.set_obm_from_symmetric(obmol, result)
        write_ob_molecule(obmol, format, f, legacy=True)
        if format == 'pdb':
            f.write("END\n")

    def obm_from_result(self, result):
        obmols = MoleculeReader._obm_from_strings(result.molecule._file_content,
                                                  result.molecule._format,
                                                  result.molecule._babel_bond)
        self._atom_indices=[]

        for mol_index, obmol in enumerate(obmols):
            num_atoms=obmol.NumAtoms()
            for atom_index in range(num_atoms):
                self._atom_indices.append((mol_index, atom_index))

        for to_remove in result.molecule._deleted_atom_indices:
            mol_index, atom_index = self._atom_indices[to_remove]
            obmol=obmols[mol_index]
            obmol.DeleteAtom(obmol.GetAtom(atom_index + 1))

        return obmols

    def set_obm_from_original(self, obmol, result):
        num_atoms = obmol.NumAtoms()
        # update coordinates
        for i in range(num_atoms):
            try:
                atom = obmol.GetAtom(i + 1)
                atom.SetVector(non_negative_zero(result.molecule.atoms[i].pos[0]),
                               non_negative_zero(result.molecule.atoms[i].pos[1]),
                               non_negative_zero(result.molecule.atoms[i].pos[2]))
            except Exception as e:
                pass
        return obmol

    def set_obm_from_symmetric(self, obmol, result):
        num_atoms = obmol.NumAtoms()
        for i in range(num_atoms):
            try:
                a = obmol.GetAtom(i + 1)
                a.SetVector(non_negative_zero(result.symmetric_structure[i][0]),
                            non_negative_zero(result.symmetric_structure[i][1]),
                            non_negative_zero(result.symmetric_structure[i][2]))
            except Exception as e:
                pass
        return obmol




# resultwriters
class ResultWriter:
    """
    A class for writing results. It can write molecules to various openbabel and CSM formats, 
    can write headers, local csm, permutation, etc. Most functions prefixed write_ expect a filestream. 
    The two print functions may be changed in the future but for now print to the screen
    Inheriting classes are recommended to inherit a write() function that can be called from main()
    """

    def __init__(self, result, format, print_local=False, *args, **kwargs):
        self.result = result
        self.op_name = result.operation.name
        self.format = str.lower(format)
        self.print_local = print_local
        self.result_string = self.get_result_string()

    def write(self):
        raise NotImplementedError

    def get_result_string(self):
        result_io = io.StringIO()
        self._write_results(result_io)
        result_string = result_io.getvalue()
        result_io.close()
        return result_string

    def to_dict(self):
        json_dict = {"Result":
            {
                "result_string": self.result_string,
                "molecule": self.result.molecule.to_dict(),
                "op_order": self.result.op_order,
                "op_type": self.result.op_type,
                "csm": self.result.csm,
                "perm": self.result.perm,
                "dir": list(self.result.dir),
                "d_min": self.result.d_min,
                "symmetric_structure": [list(i) for i in self.result.symmetric_structure],
                "local_csm": self.result.local_csm,
                "perm_count": self.result.perm_count,
                "formula_csm": self.result.formula_csm,
                "normalized_molecule_coords": [list(i) for i in self.result.normalized_molecule_coords],
                "normalized_symmetric_structure": [list(i) for i in self.result.normalized_symmetric_structure],
            }
        }
        return json_dict

    def _write_results(self, f):
        self.write_header(f)
        self.write_mol(f)
        self.write_dir(f)

        if self.print_local:
            self.write_local_csm(f)

        if self.op_name == "CHIRALITY":
            self.write_chirality(f)

        self.write_permutation(f)

    def write_header(self, f):
        f.write("%s: %s\n" % (self.op_name, format_CSM(self.result.csm)))
        f.write("SCALING FACTOR: %7lf\n" % non_negative_zero(self.result.d_min))

    def write_mol(self, f):
        if self.format == "csm":
            molwriter = CSMMolWriter()
        else:
            molwriter = OBMolWriter()

        molwriter.write(f, self.result, self.op_name, self.format)

    def write_dir(self, f):
        f.write("\n DIRECTIONAL COSINES:\n\n")
        f.write("%lf %lf %lf\n" % (
            non_negative_zero(self.result.dir[0]), non_negative_zero(self.result.dir[1]),
            non_negative_zero(self.result.dir[2])))

    def write_local_csm(self, f):
        sum = 0
        f.write("\nLocal CSM: \n")
        size = len(self.result.molecule.atoms)
        for i in range(size):
            sum += self.result.local_csm[i]
            f.write("%s %7lf\n" % (self.result.molecule.atoms[i].symbol, non_negative_zero(self.result.local_csm[i])))
        f.write("\nsum: %7lf\n" % sum)

    def write_chirality(self, f):
        if self.result.operation.type == 'CS':
            f.write("\n MINIMUM CHIRALITY WAS FOUND IN CS\n\n")
        else:
            f.write("\n MINIMUM CHIRALITY WAS FOUND IN S%d\n\n" % self.result.operation.order)

    def write_permutation(self, f):
        f.write("\n PERMUTATION:\n\n")
        for i in self.result.perm:
            f.write("%d " % (i + 1))
        f.write("\n")

    def print_structure(self):
        # print CSM, initial molecule, resulting structure and direction according to format specified
        try:
            percent_structure = check_perm_structure_preservation(self.result.molecule, self.result.perm)
            print("The permutation found maintains",
                  str(round(percent_structure * 100, 2)) + "% of the original molecule's structure")

        except ValueError:
            print(
                "The input molecule does not have bond information and therefore conservation of structure cannot be measured")

        if True:  # falsecount > 0 or self.dictionary_args['calc_type'] == 'approx':
            print(
                "The permutation found contains %d invalid %s. %.2lf%% of the molecule's atoms are in legal cycles" % (
                    self.result.falsecount, "cycle" if self.result.falsecount == 1 else "cycles",
                    100 * (len(self.result.molecule) - self.result.num_invalid) / len(self.result.molecule)))
            for cycle_len in sorted(self.result.cycle_counts):
                valid = cycle_len == 1 or cycle_len == self.result.op_order or (
                    cycle_len == 2 and self.result.op_type == 'SN')
                count = self.result.cycle_counts[cycle_len]
                print("There %s %d %s %s of length %d" % (
                    "is" if count == 1 else "are", count, "invalid" if not valid else "",
                    "cycle" if count == 1 else "cycles",
                    cycle_len))

    def print_result(self):
        print("%s: %s" % (self.op_name, format_CSM(self.result.csm)))
        print("CSM by formula: %s" % (format_CSM(self.result.formula_csm)))

    def print_chain_perm(self):
        if len(self.result.molecule.chains)>1:
            print("Chain perm: ", self.result.chain_perm_string())

class ApproxStatisticWriter:
    def __init__(self, statistics, stat_file_name, polar):
        self.statistics=statistics
        self.file_name = stat_file_name
        self.polar = polar


    def write(self):
        with open(self.file_name, 'w') as file:
            if self.polar:
                file.write("Index"
                        "\tr_i\tth_i\tph_i"
                       "\tCSM_i"
                       "\tr_f\tth_f\tph_f"
                       "\tCSM_f"
                        "\tRuntime"
                        "\t # Iter"
                        "\t Stop Reason"
                        "\n")
            else:
                file.write("Index\t"
                        "x_i\ty_i\tz_i"
                       "\tCSM_i"
                       "\tx_f\ty_f\tz_f"
                       "\tCSM_f"
                        "\tRuntime"
                        "\t # Iter"
                        "\t Stop Reason"
                        "\n")
            for index, key in enumerate(self.statistics):
                start_str=str(index) +"\t"
                try:
                    stat=self.statistics[key]
                    x,y,z=stat.start_dir
                    start_str =start_str + format_CSM(x)+ "\t"+format_CSM(y)+ "\t"+format_CSM(z)+ "\t"
                    xf,yf,zf=stat.end_dir
                    if self.polar:
                        x,y,z=cart2sph(x,y,z)
                        xf,yf,zf=cart2sph(xf,yf,zf)

                    file.write(start_str
                               + format_CSM(stat.start_csm)+"\t"
                               + format_CSM(xf) + "\t" + format_CSM(yf) + "\t" + format_CSM(zf) + "\t"
                               + format_CSM(stat.end_csm) + "\t"
                               + format_CSM(stat.run_time) + "\t"
                               + str(stat.num_iterations) + "\t"
                               + stat.stop_reason +
                               "\n")
                except:
                    file.write(start_str + "failed to read statistics\n")

class OldFormatFileWriter(ResultWriter):
    """
    A ResultWriter class that writes to a file 
    """

    def __init__(self, result, out_file_name, print_local=False, json_output=False, out_format=None, *args, **kwargs):
        self.out_file_name = out_file_name
        self.json_output = json_output
        if not out_format:
            try:
                out_format = get_format(None, result.molecule._format)
            except ValueError:
                out_format = get_format(None, out_file_name)
        super().__init__(result, out_format, print_local)

    def write(self):
        self.print_structure()
        self.print_result()
        self.print_chain_perm()
        if self.json_output:
            with open(self.out_file_name, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f)
        else:
            with open(self.out_file_name, 'w', encoding='utf-8') as f:
                self._write_results(f)

class ScriptWriter:
    def __init__(self, results, format, out_file_name=None, **kwargs):
        '''
        :param results: an array of arrays of CSMResults
        :param format: molecule format to output to
        :param out_file_name: if none is provided, the current working directory/csm_results will be used
        '''
        self.results=results
        self.format=format
        if not out_file_name:
            out_file_name=os.path.join(os.getcwd(), 'csm_results')
        if not os.path.isdir(out_file_name):
            os.mkdir(out_file_name)
        self.folder=out_file_name

    def write(self):
        self.create_CSM_tsv()
        self.create_perm_tsv()
        self.create_dir_tsv()
        self.create_extra_tsv()
        self.create_extra_txt()
        self.create_approx_statistics()
        self.create_legacy_files()
        self.create_symm_mols()
        self.create_initial_mols()

    def create_CSM_tsv(self):
    #creates a tsv file with CSM per molecule
        filename = os.path.join(self.folder, "csm.txt")
        with open(filename, 'w') as f:
            f.write("\t")
            for index in range(len(self.results[0])):
                f.write("cmd" + str(index) + "\t")
            f.write("\n")
            for index, mol_results in enumerate(self.results):
                f.write("Molecule "+str(index))
                for result in mol_results:
                    f.write("\t"+format_CSM(result.csm))
                f.write("\n")

    def create_perm_tsv(self):
        #creates a tsv for permutations (needs to handle extra long permutations somehow)
        filename = os.path.join(self.folder, "perms.tsv")
        with open(filename, 'w') as f:
            for mol_index, mol_results in enumerate(self.results):
                for line_index, command_result in enumerate(mol_results):
                    f.write(str(mol_index)+"\tL_"+str(line_index)+"\t")
                    f.write("\t")
                    write_array_to_file(f, command_result.perm, True)
                    f.write("\n")

    def create_dir_tsv(self):
        filename = os.path.join(self.folder, "dirs.tsv")
        with open(filename, 'w') as f:
            for mol_index, mol_results in enumerate(self.results):
                for line_index, command_result in enumerate(mol_results):
                    f.write(str(mol_index)+"\tL_"+str(line_index)+"\t")
                    f.write("\t")
                    write_array_to_file(f, command_result.dir, separator="\t")
                    f.write("\n")

    def create_extra_tsv(self):
        #create headers
        #first row: cmd
        header_lines_1="\t"
        header_lines_2="\n\t"
        for line_index, command_result in enumerate(self.results[0]):
                for key in sorted(command_result.overall_statistics):
                    header_lines_1+="cmd"+str(line_index)+"\t"
                    header_lines_2 += key + "\t"

        filename = os.path.join(self.folder, "extra.tsv")
        with open(filename, 'w') as f:
            f.write(header_lines_1+header_lines_2+"\n")
            for mol_index, mol_results in enumerate(self.results):
                f.write("mol"+str(mol_index)+"\t")
                for line_index, command_result in enumerate(mol_results):
                    for key in sorted(command_result.overall_statistics):
                        f.write(str(command_result.overall_statistics[key]))
                        f.write("\t")
                f.write("\n")

    def create_approx_statistics(self):
        #(in approx there's also a table with initial direction, initial CSM, final direction, final CSM, number iterations, run time, and stop reason for each direction in approx)
        #create headers
        #first row: cmd

        #first, check that at least one of the commands has running statistics:
        has_ongoing=False
        for command_result in self.results[0]:
            if command_result.ongoing_statistics:
                has_ongoing=True

        if not has_ongoing:
            return

        out_folder=os.path.join(self.folder, 'approx')
        if not os.path.isdir(out_folder):
            os.mkdir(out_folder)


        for mol_index, mol_results in enumerate(self.results):
            for line_index, command_result in enumerate(mol_results):
                name="mol"+str(mol_index)+"_cmd"+str(line_index)
                filename=os.path.join(out_folder, name+".tsv")
                if command_result.ongoing_statistics:
                    self._write_approx_statistics(filename, command_result.ongoing_statistics["approx"])

    def _write_approx_statistics(self, filename, stats):
        with open (filename, 'w') as f:
            self.polar = False
            if self.polar:
                f.write("Dir Index"
                        "\tr_i\tth_i\tph_i"
                        "\tCSM_i"
                        "\tr_f\tth_f\tph_f"
                        "\tCSM_f"
                        "\tRuntime"
                        "\t # Iter"
                        "\t Stop Reason"
                        "\n")
            else:
                f.write("Dir Index"
                        "\tx_i\ty_i\tz_i"
                        "\tCSM_i"
                        "\tx_f\ty_f\tz_f"
                        "\tCSM_f"
                        "\tRuntime"
                        "\t # Iter"
                        "\tStop Reason"
                        "\n")

            for direction_index, direction_dict in enumerate(stats):
                dir = direction_dict['dir']
                stat = direction_dict['stats']
                start_str = str(direction_index) + "\t"
                try:
                    x, y, z = stat['start dir']
                    start_str = start_str + format_CSM(x) + "\t" + format_CSM(y) + "\t" + format_CSM(z) + "\t"
                    xf, yf, zf = stat['end dir']
                    if self.polar:
                        x, y, z = cart2sph(x, y, z)
                        xf, yf, zf = cart2sph(xf, yf, zf)

                    f.write(start_str
                            + format_CSM(stat['start csm']) + "\t"
                            + format_CSM(xf) + "\t" + format_CSM(yf) + "\t" + format_CSM(zf) + "\t"
                            + format_CSM(stat['end csm']) + "\t"
                            + format_CSM(stat['run time']) + "\t"
                            + str(stat['num iterations']) + "\t"
                            + stat['stop reason'] + "\t"
                                                    "\n")
                except Exception as e:
                    try:
                        start_str = start_str + stat['stop reason'] + "\t"
                    finally:
                        f.write(start_str + "failed to read statistics\n")

    def create_extra_txt(self):
        def print_structure(f, result):
            # print CSM, initial molecule, resulting structure and direction according to format specified
            try:
                percent_structure = check_perm_structure_preservation(result.molecule, result.perm)
                f.write("The permutation found maintains"+
                      str(round(percent_structure * 100, 2)) + "% of the original molecule's structure")

            except ValueError:
                f.write(
                    "The input molecule does not have bond information and therefore conservation of structure cannot be measured")

            if True:  # falsecount > 0 or self.dictionary_args['calc_type'] == 'approx':
                falsecount, num_invalid, cycle_counts, bad_indices = check_perm_cycles(result.perm, result.operation.order,
                                                                                       result.operation.type)
                f.write(
                    "The permutation found contains %d invalid %s. %.2lf%% of the molecule's atoms are in legal cycles" % (
                        falsecount, "cycle" if falsecount == 1 else "cycles",
                        100 * (len(result.molecule) - num_invalid) / len(result.molecule)))

                for cycle_len in sorted(cycle_counts):
                    valid = cycle_len == 1 or cycle_len == result.operation.order or (
                            cycle_len == 2 and result.operation.type == 'SN')
                    count = cycle_counts[cycle_len]
                    f.write("\nThere %s %d %s %s of length %d" % (
                        "is" if count == 1 else "are", count, "invalid" if not valid else "",
                        "cycle" if count == 1 else "cycles",
                        cycle_len))

        #2. the equivalence class and chain information (number and length)
        #4. Cycle numbers and lengths
        filename = os.path.join(self.folder, "extra.txt")
        with open(filename, 'w') as f:
            for mol_index, mol_results in enumerate(self.results):
                f.write("mol"+str(mol_index)+"\n")
                mol_results[0].molecule.print_equivalence_class_summary(True, f)
                f.write("\n")
                for line_index, command_result in enumerate(mol_results):
                    f.write("cmd"+str(line_index)+"\n")
                    if len(command_result.molecule.chains) > 1:
                        f.write("\nChain perm: "+ command_result.chain_perm_string)
                    print_structure(f, command_result)
                f.write("\n-----------------------------\n")


    def create_legacy_files(self):
        out_folder=os.path.join(self.folder, 'legacy')
        if not os.path.isdir(out_folder):
            os.mkdir(out_folder)
        for mol_index, mol_results in enumerate(self.results):
            for line_index, command_result in enumerate(mol_results):
                file_name="mol"+str(mol_index)+"_cmd"+str(line_index)+".txt"
                out_file_name= os.path.join(out_folder, file_name)
                of=OldFormatFileWriter(command_result, out_file_name, out_format=self.format)
                with open(out_file_name, 'w', encoding='utf-8') as f:
                    of._write_results(f)

    def mult_mol_writer(self, filename, obmols):
        '''
        :param filename:
        :param obmols:
        :return:
        '''

        if len(obmols)>1:
            if self.format=="mol":
                string=""
                for mol in obmols:
                    string+=mol_string_from_obm(mol, self.format)
                    string+="\n$$$$\n"
                with open(filename, 'w') as file:
                    file.write(string)
                return

            elif self.format=="pdb":
                string=""
                for mol in obmols:
                    string+=mol_string_from_obm(mol, self.format)
                string.replace("END", "ENDMDL")
                string+="\nEND"
                with open(filename, 'w') as file:
                    file.write(string)
                return

        #default, including for multiple obmols that aren't special case formats above
        with open(filename, 'w') as file:
            for mol in obmols:
                write_ob_molecule(mol, self.format, file)


    def create_initial_mols(self):
        # chained file of initial structures
        filename = os.path.join(self.folder, "initial_normalized_coordinates." + self.format)
        for mol_results in self.results:
            for result in mol_results:
                obmolwriter = OBMolWriter()
                obmols = obmolwriter.obm_from_result(result)
                for obmol in obmols:
                    obmolwriter.set_obm_from_original(obmol, result)
                self.mult_mol_writer(filename, obmols)

    def create_symm_mols(self):
        # chained file of symmetric structures
        filename = os.path.join(self.folder, "resulting_symmetric_coordinates." + self.format)
        for mol_results in self.results:
            for result in mol_results:
                obmolwriter = OBMolWriter()
                obmols = obmolwriter.obm_from_result(result)
                for obmol in obmols:
                    obmolwriter.set_obm_from_original(obmol, result)
                self.mult_mol_writer(filename, obmols)





