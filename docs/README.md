## luna-soc Documentation

### Rebuilding register diagrams

After peripheral changes the register diagrams can be rebuilt with:

    make registers

### Rebuilding sequence diagrams

Before rebuilding the sequence diagrams you will need to install the [d2](https://github.com/terrastruct/d2) compiler.

After making any changes to the sequence diagrams they can be rebuilt with:

    make d2
