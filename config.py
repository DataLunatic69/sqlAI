def config(filename='database.ini', section='postgresql'):
    from configparser import ConfigParser

   
    parser = ConfigParser()

    
    parser.read(filename)
    print(f"Sections found: {parser.sections()}")  

    
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
        print(f"Parameters retrieved: {db}")  
    else:
        raise Exception(f"Section {section} not found in the {filename} file")

    return db
