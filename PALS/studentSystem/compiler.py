import subprocess, tempfile, textwrap, os, sys, re

# Write an sml code snippet to a file and run it using SML/NJ
sml_code = textwrap.dedent("""fun add (x, y) = x + y;
val result = add(3, 4);
print(Int.toString(result) ^ "\\n");""")

with open("fact.sml", "w", encoding="utf-8") as f:
    f.write(sml_code)

# Run SML/NJ with the code file
feed = f'use "{"fact.sml"}";\n'         

result = subprocess.run(
    ["sml"],
    input = feed,
    text  = True,
    capture_output = True,
    check = True,
    shell=True,                     
)

def process_result(result):
    # Clean up the result by removing leading autoloading messages
    output = result.stdout.strip()
    output = output.splitlines()
    autoloaded = output.index("[autoloading done]")
    output = output[autoloaded + 1:]

    full_string = ""
    for x in output:
        full_string = full_string + "\n" + x


    return full_string

def clean(stdout: str) -> list[str]:
    # Clean up the rest of the result by removing all messages not relevant to the code output
    NOISE = re.compile(r"""
        ^\s*val\s            #  val …         (bindings)
    | ^\s*-\s*$            #  -             (continuation prompt)
    | ^\s*$                #  blank line
    """, re.VERBOSE)

    return [ln for ln in stdout.splitlines()
            if not NOISE.match(ln)]

first_process = process_result(result)

print("----- SML/NJ STDOUT -----")
for line in clean(first_process):
    print(line)
print("-------------------------")
