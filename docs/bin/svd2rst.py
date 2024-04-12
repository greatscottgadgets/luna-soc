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

    # output table header
    f.write(f".. list-table:: {peripheral_name} Register Map\n")
    f.write(f"  :header-rows: 1\n")
    f.write("\n")
    f.write("  * - Offset\n")
    f.write("    - Range\n")
    f.write("    - Access\n")
    f.write("    - Name\n")
    f.write("    - Description\n")

    peripheral = [p for p in svd.findall("peripherals/peripheral") if p.find("name").text == peripheral_name]
    if len(peripheral) == 0:
        print(f"Failed to find peripheral: {peripheral_name}")
        sys.exit(1)
    peripheral = peripheral[0]

    registers = peripheral.findall("registers/register")
    for register in registers:
        offset = register.find("addressOffset").text
        access = register.find("access").text

        fields = register.findall("fields/field")
        for field in fields:
            size = field.find("bitRange").text
            name = field.find("name").text
            description = field.find("description").text.strip().replace("\n", "")

            f.write(f"  * - {offset}\n")
            f.write(f"    - {size}\n")
            f.write(f"    - {access}\n")
            f.write(f"    - ``{name}``\n")
            f.write(f"    - {description}\n")

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
