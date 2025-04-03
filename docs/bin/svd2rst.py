import io, os, sys


from xml.dom.minidom import parse

import xml.etree.ElementTree as ET


def svd2rst(peripheral_name, input, output=None):
    # parse svd file
    svd = ET.parse(input)

    # create output file
    if output is None:
        f = io.StringIO()
    else:
        f = open(output, 'w')

    peripheral = [p for p in svd.findall("peripherals/peripheral") if p.find("name").text == peripheral_name]
    if len(peripheral) == 0:
        print(f"Failed to find peripheral: {peripheral_name}")
        sys.exit(1)
    peripheral = peripheral[0]

    registers = peripheral.findall("registers/register")
    for register in registers:
        offset        = register.find("addressOffset").text
        register_name = register.find("name").text.upper()
        description   = register.find("description").text

        # output register name
        f.write("\n")
        f.write(f"**{register_name} Register**\n")
        f.write("\n")

        # output table headers
        f.write(f".. list-table::\n")
        f.write(f"  :widths: 100 100 100 500\n")
        f.write(f"  :header-rows: 1\n")
        f.write("\n")
        f.write("  * - Offset\n")
        f.write("    - Range\n")
        f.write("    - Access\n")
        f.write("    - Field\n")

        # output table rows
        fields = register.findall("fields/field")
        for field in fields:
            size = field.find("bitRange").text
            name = field.find("name").text
            access = field.find("access").text
            if name.startswith("_"):
                continue

            f.write(f"  * - {offset}\n")
            f.write(f"    - {size}\n")
            f.write(f"    - {access}\n")
            f.write(f"    - ``{name}``\n")

        # output register documentation
        if register_name.startswith("EV_"):
            continue
        f.write("\n")
        f.write(".. code-block:: markdown\n")
        f.write("\n")
        f.write(f"    {description}\n")
        f.write("\n")

    if output is None:
        print(f.getvalue())
    f.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: svd2rst <peripheral name> <svd input file> [rst output file]")
        sys.exit(1)

    peripheral = sys.argv[1]
    input      = sys.argv[2]

    if len(sys.argv) == 4:
        output =  sys.argv[3]
    else:
        output = None

    svd2rst(peripheral, input, output)
