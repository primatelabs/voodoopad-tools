import os
import sys


def main():

    if len(sys.argv) != 3 and len(sys.argv) != 4:
        print('usage: voodoopad_import.py <document> <directory> <password>')
        return

    document = sys.argv[1]
    directory = sys.argv[2]

    if len(sys.argv) == 4:
        password = sys.argv[3]
    else:
        password = None

    files = os.listdir(directory)

    for f in files:
        article_name = os.path.splitext(f)[0]
        file_path = directory + '/' + f

        if password != None:
            cmdline = 'python3 voodoopad.py {0} add {1} {2} markdown --password {3}'.format(document, file_path, article_name, password)
        else:
            cmdline = 'python3 voodoopad.py {0} add {1} {2} markdown'.format(document, file_path, article_name)

        print(cmdline)
        os.system(cmdline)

if __name__ == '__main__':
    main()
