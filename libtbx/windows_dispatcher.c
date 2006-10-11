#include <process.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

/* Unique strings generated with: libtbx.obfuscate
 */

static const char* /* WINDOWS_DISPATCHER interleaved with random digits */
unique_pattern = "0W6I0N6D0O2W8S5_0D0I8S1P4A3T6C4H9E4R7";

static char* /* LIBTBX_BUILD interleaved with random digits */
libtbx_build = "LIBTBX_BUILD="
"3L0I2B2T9B4X2_8B5U5I5L2D4_3L0I2B2T9B4X2_8B5U5I5L2D4_3L0I2B2T9B4X2_8B5U5I5L2D4"
"_3L0I2B2T9B4X2_8B5U5I5L2D4_3L0I2B2T9B4X2_8B5U5I5L2D4_3L0I2B2T9B4X2_8B5U5I5L2D"
"4_3L0I2B2T9B4X2_8B5U5I5L2D4_3L0I2B2T9B4X2_8B5U5I5L2D4_3L0I2B2T9B4X2_8B5U5I5L2"
"D4_3L0I2B2T9B4X2_8B5U5I5";

static char* /* LIBTBX_DISPATCHER_NAME interleaved with random digits */
libtbx_dispatcher_name = "LIBTBX_DISPATCHER_NAME="
"6L6I7B2T3B2X5_6D8I7S0P2A0T5C8H1E8R3_1N0A9M9E5_6L6I7B2T3B2X5_6D8I7S0P2A0T5C8H";

static char* /* PYTHON_EXECUTABLE interleaved with random digits */
python_executable =
"5P2Y5T7H2O5N8_0E7X9E7C8U6T4A9B9L5E3_5P2Y5T7H2O5N8_0E7X9E7C8U6T4A9B9L5E3_5P2Y5"
"T7H2O5N8_0E7X9E7C8U6T4A9B9L5E3_5P2Y5T7H2O5N8_0E7X9E7C8U6T4A9B9L5E3_5P2Y5T7H2O"
"5N8_0E7X9E7C8U6T4A9B9L5E3_5P2Y5T7H2O5N8_0E7X9E7C8U6T4A9B9L5E3_5P2Y5T7H2O5N8_0"
"E7X9E7C8U6T4A9B9L5E3_5P2";

static char* /* PYTHONPATH interleaved with random digits */
pythonpath =
"2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2"
"N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_"
"2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2"
"N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_"
"2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2"
"N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_"
"2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2"
"N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_"
"2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2"
"N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_"
"2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2"
"N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_"
"2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2"
"N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_"
"2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2"
"N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_"
"2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2"
"N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_"
"2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2"
"N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_"
"2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2"
"N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_"
"2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2"
"N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_"
"2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2"
"N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_"
"2P0Y1T7H3O2N7P7A2T5H8_2P0Y1T7H3O2N7P7A2T5H8_2";

static char* /* MAIN_PATH interleaved with random digits */
main_path =
"1M5A1I0N4_8P7A0T9H9_1M5A1I0N4_8P7A0T9H9_1M5A1I0N4_8P7A0T9H9_1M5A1I0N4_8P7A0T9"
"H9_1M5A1I0N4_8P7A0T9H9_1M5A1I0N4_8P7A0T9H9_1M5A1I0N4_8P7A0T9H9_1M5A1I0N4_8P7A"
"0T9H9_1M5A1I0N4_8P7A0T9H9_1M5A1I0N4_8P7A0T9H9_1M5A1I0N4_8P7A0T9H9_1M5A1I0N4_8"
"P7A0T9H9_1M5A1I0N4_8P7A0T9H9_1M5A1I0N4_8P7A0T9H9_1M5A1I0N4_8P7A0T9H9_1M5A1I0N"
"4_8P7A0T9H9_1M5A1I0N4_8P7A0T9H9_1M5A1I0N4_8P7A0T9H9_1M5A1I0N4_8P7A0T9H9_1M5A1"
"I0N4_8P7A0T9H9_1M5A1I0N4_8P7A0T9H9_1M5A1I0N4_8P7A0T9H9_1M5A1I0N4_8P7A0T9H9_1M"
"5A1I0N4_8P7A0T9H9_1M5A1I0N4_8P7A0T9H9_1M5A1I0N4_8P";

static char* /* TARGET_COMMAND interleaved with random digits */
target_command =
"5T4A3R7G8E3T7_6C5O0M0M3A8N8D2_5T4A3R7G8E3T7_6C5O0M0M3A8N8D2_5T4A3R7G8E3T7_6C5"
"O0M0M3A8N8D2_5T4A3R7G8E3T7_6C5O0M0M3A8N8D2_5T4A3R7G8E3T7_6C5O0M0M3A8N8D2_5T4A"
"3R7G8E3T7_6C5O0M0M3A8N8D2_5T4A3R7G8E3T7_6C5O0M0M3A8N8D2_5T4A3R7G8E3T7_6C5O0M0"
"M3A8N8D2_5T4A3R7G8E3T7_6";

int
is_py(const char* path)
{
  int n, i;
  n = strlen(path);
  if (n < 3) return 0;
  n -= 3;
  for(i=0;i<3;i++,n++) {
    if (tolower(path[n]) != ".py"[i]) return 0;
  }
  return 1;
}

void*
malloc_certain(const char* argv0, unsigned long n)
{
  void* ptr;
  errno = 0;
  ptr = malloc(n);
  if (ptr == NULL) {
    fprintf(stderr, "%s: error allocating %lu bytes", argv0, n);
    if (errno) {
      fprintf(stderr, ": %s", strerror(errno));
    }
    fprintf(stderr, "\n");
    exit(2);
  }
  return ptr;
}

void
prepend_path_element(
  const char* argv0,
  const char* var_name,
  const char* additional_element)
{
  const char* original_value;
  char* buffer;
  size_t sz;
  original_value = getenv(var_name);
  sz = strlen(var_name) + 1 + strlen(additional_element) + 1;
  if (original_value != NULL) sz += 1 + strlen(original_value);
  buffer = malloc_certain(argv0, sz);
  strcpy(buffer, var_name);
  strcat(buffer, "=");
  strcat(buffer, additional_element);
  if (original_value != NULL) {
    strcat(buffer, ";");
    strcat(buffer, original_value);
  }
  _putenv(buffer);
}

int
main(int argc, char *const argv[])
{
  char** extended_argv;
  int n, i;
  _putenv("PYTHONHOME=");
  _putenv("PYTHONCASEOK=1");
  _putenv(libtbx_build);
  _putenv(libtbx_dispatcher_name);
  prepend_path_element(argv[0], "PYTHONPATH", pythonpath);
  prepend_path_element(argv[0], "PATH", main_path);
  extended_argv = malloc_certain(argv[0], (argc + 2) * sizeof(char*));
  n = 0;
  if (is_py(target_command)) {
    extended_argv[n++] = python_executable;
  }
  extended_argv[n++] = target_command;
  for(i=1;i<argc;i++,n++) {
    extended_argv[n] = malloc_certain(argv[0], strlen(argv[i]) + 3);
    strcpy(extended_argv[n], "\"");
    strcat(extended_argv[n], argv[i]);
    strcat(extended_argv[n], "\"");
  }
  extended_argv[n] = NULL;
  _flushall();
  _fileinfo = 1;
  _spawnv(_P_WAIT, extended_argv[0], extended_argv);
  if (errno) {
    fprintf(stderr, "%s: error starting %s: %s\n",
      argv[0], extended_argv[0], strerror(errno));
    exit(3);
  }
  return 0;
}
