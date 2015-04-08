/*
 * Implementation of the thin wrapper around boost::log
 *
 * Developed by Itay Zandbank
 */

#include "logging.h"

#ifdef __APPLE__

#include <iostream>
#include <string>
using namespace std;

ofstream null_output;

void set_file_logging(std::string path)
{
    // No file logging
}

void init_logging()
{
    null_output.open("/dev/null");
}

#else

#include <boost/log/utility/setup/console.hpp>
#include <boost/log/utility/setup/file.hpp>
#include <boost/log/utility/setup/common_attributes.hpp>
#include <boost/log/sources/logger.hpp>
#include <boost/log/trivial.hpp>
#include <boost/log/trivial.hpp>

using namespace boost::log;

static void set_debug_logging(bool enable)
{
	if (enable)
        core::get()->set_filter(trivial::severity >= trivial::trace);
	else
		core::get()->set_filter(trivial::severity >= trivial::info);
}

void init_logging()
{
	add_common_attributes();
	register_simple_formatter_factory< trivial::severity_level, char >("Severity");
	add_console_log(std::cerr,
		keywords::format = "[%TimeStamp%]  [%Severity%]: %Message%",
		keywords::filter = trivial::severity >= trivial::error);
	add_console_log(std::cout, keywords::format = "%Message%");

	set_debug_logging(false);
}

void set_file_logging(std::string path)
{
	add_file_log(path,
		keywords::open_mode = std::ios_base::app,
		keywords::auto_flush = true,
		keywords::format = "[%TimeStamp%]  [%Severity%]: %Message%");
	set_debug_logging(true);
}

#endif