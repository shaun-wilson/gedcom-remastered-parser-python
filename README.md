# GEDCOM Remastered Parser (Python)
A Python 3 package that parses a [GEDCOM Remastered Standard](https://github.com/shaun-wilson/gedcom-remastered), and generates an object model.

The schema knows how to read and write it's elements to files, and the output should be syntactically equal to the original.

The package will have the ability to modify the schema, whether by adding, removing, or altering existing definitions.

This package does not parse actual GEDCOM files, and does not validate GEDCOM data. This functionality will be created in another package.

    from gedcom_remastered_parser import Schema

    schema = Schema.generate_from_files(
        [
            'https://raw.githubusercontent.com/shaun-wilson/gedcom-remastered/gedcom-5.5.1/gedcom-5.5.1-structures.txt',
            'https://raw.githubusercontent.com/shaun-wilson/gedcom-remastered/gedcom-5.5.1/gedcom-5.5.1-primitives.txt',
            'https://raw.githubusercontent.com/shaun-wilson/gedcom-remastered/gedcom-5.5.1/gedcom-5.5.1-tags.txt',
        ]
    )
    
    # Ensure the schema round-trips correctly.
    for element_type in ("structures", "primitives", "tags"):
        with open(f"regen-{element_type}.txt", 'w') as file_writer:
            file_writer.write( "\n".join(element.txt_definition for element in getattr(schema, element_type).values()) )
