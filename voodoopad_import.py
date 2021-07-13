import os
import sys


def main():

  if len(sys.argv) != 3:
    print('usage: voodoopad_import.py <document> <directory>')
    return

  document = sys.argv[1]
  directory = sys.argv[2]

  files = os.listdir(directory)

  for f in files:
    article_name = os.path.splitext(f)[0]
    file_path = directory + '/' + f


    cmdline = 'python3 voodoopad.py {0} add {1} {2} markdown'.format(document, file_path, article_name)
    print(cmdline)
    os.system(cmdline)

if __name__ == '__main__':
  main()