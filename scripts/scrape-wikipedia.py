import os
import sys
import wikilink
import tempfile
import urllib.parse
import subprocess

# TODO: Is there a way to automatically find this script?
converter_path = '/home/brichard/git/mediawiki-to-markdown/convert.php'

def get_article_markdown(article_name):

  file_name = wikilink.convert_link(article_name) + '.xml'

  pwd = os.getcwd() + '/'
  tmp_dir = pwd + 'tmp/'

  # The mediawiki to markdown script does not let us specify the output file name. It only lets us specify the
  # directory. So we create a temporary directory and output the markdown file to it. Since it will be the
  # only file in the directory, we can read it back without knowing its name.
  md_dir = tempfile.TemporaryDirectory()

  url = 'https://en.wikipedia.org/wiki/Special:Export/{0}'.format(urllib.parse.quote(article_name))

  subprocess.Popen("curl -L {0} --output {1}".format(url, tmp_dir + file_name), shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).wait()
  subprocess.Popen('php {0} --filename={1} --format=markdown_strict --output={2}'.format(converter_path, tmp_dir + file_name, md_dir.name), shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).wait()

  md_path = md_dir.name + '/' + os.listdir(md_dir.name)[0]

  try:
    with open(md_path, 'rb') as f:
      md_text = f.read().decode('utf-8')
  except:
    return None

  md_dir.cleanup()

  return md_text

def main():

  # Verify converter is installed
  if not os.path.exists(converter_path):
    print('Error: Could not find mediawiki converter: ', converter_path)
    return

  if len(sys.argv) != 3:
    print('Uasge: <article name> <output directory>')
    return

  article_name = sys.argv[1]
  output_dir = sys.argv[2]
  
  os.system('mkdir -p {0}'.format(output_dir))
  os.system('mkdir -p tmp')
  
  article = get_article_markdown(article_name)

  if article == None:
    print('Could not find article for ', article_name)
    return

  converted_article = wikilink.convert_article(article)

  file_name = output_dir + '/' + wikilink.convert_link(article_name) + '.md'

  print(file_name)
  with open(file_name, 'wt') as f:
    f.write(converted_article)

  # Get all the links from this article

  links = wikilink.get_links(article)

  # Download every article this one links to
  for link in links:
    article_name = link

    try:
      article_text = get_article_markdown(article_name)
      if article_text == None:
        print('Error getting article for ', article_name)
        continue
    except:
      continue

    converted_article = wikilink.convert_article(article_text)
    file_name = output_dir + '/' + wikilink.convert_link(article_name) + '.md'

    print(file_name)
    with open(file_name, 'wt') as f:
      f.write(converted_article)

if __name__ == '__main__':
  main()
