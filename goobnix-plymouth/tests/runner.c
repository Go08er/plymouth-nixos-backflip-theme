/* Exercise the installed theme using Plymouth's real script interpreter.
 * Display/image APIs are mocked: no daemon, root privileges or VT required. */
#include <stdio.h>
#include <stdlib.h>
#include "script.h"
#include "script-execute.h"
#include "script-object.h"
#include "script-parse.h"

static unsigned checks;

static script_return_t check(script_state_t *state, void *unused)
{
    (void) unused;
    char *label = script_obj_hash_get_string(state->local, "label");
    if (!script_obj_hash_get_bool(state->local, "condition")) {
        fprintf(stderr, "FAIL: %s\n", label);
        free(label);
        exit(1);
    }
    free(label);
    checks++;
    return script_return_obj_null();
}

int main(int argc, char **argv)
{
    if (argc != 4) {
        fprintf(stderr, "usage: script-check mocks.script theme.script assertions.script\n");
        return 2;
    }
    script_state_t *state = script_state_new(NULL);
    script_add_native_function(state->global, "Check", check, NULL,
                               "condition", "label", NULL);
    script_op_t *ops[3];
    for (int i = 0; i < 3; i++) {
        ops[i] = script_parse_file(argv[i + 1]);
        if (!ops[i]) {
            fprintf(stderr, "Could not parse %s\n", argv[i + 1]);
            return 1;
        }
        script_return_t result = script_execute(state, ops[i]);
        if (result.type != SCRIPT_RETURN_TYPE_NORMAL) {
            fprintf(stderr, "Unexpected return from %s\n", argv[i + 1]);
            return 1;
        }
        if (result.object) script_obj_unref(result.object);
    }
    script_state_destroy(state);
    for (int i = 0; i < 3; i++) script_parse_op_free(ops[i]);
    if (checks == 0) return 1;
    printf("Passed %u Plymouth script checks\n", checks);
    return 0;
}
