# voodoopad-tools


`voodoopad.py` implements some VoodooPad features.


Dump document

Builds the cache (`cache.db` inside the document directory) and prints the forward and backward links

`python3 voodoopad.py <document>`


Add a page


`python3 voodoopad.py <document> add <file> <page name>`


Export markdown - this will replace any WikiWords or document names with links to the associated document.

`python3 voodoopad.py <document> render <output directory>`


# Scripts

Scrape wikipedia

Requires MediaWiki to Markdown Converter available here [https://github.com/philipashlock/mediawiki-to-markdown](https://github.com/philipashlock/mediawiki-to-markdown)

`python3 scripts/scrape_wikipedia.py <article name> <output directory>`

Example:

`python3 scripts/scrape_wikipedia.py Napoleon napoleon_wiki`

Import the scraped Wikipedia pages into VoodooPad

`python3 scripts/voodoopad_import.py <document> <input directory>`

Example:

`python3 scripts/voodoopad_import.py Napoleon.vpdoc napoleon_wiki`


# TODO

-  Reading/writing of encrypted documents. Threre is code to decrypt documents but it is not hooked up yet
-  Create documents from scratch. Currently `voodoopad.py` only works on existing VoodooPad documents.
-  Convert markdown to HTML