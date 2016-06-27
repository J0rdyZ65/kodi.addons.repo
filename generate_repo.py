#!  /usr/bin/python

"""
    G2 Add-on
    Copyright (C) 2016 J0rdyZ65

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import os
import md5
import sys
import errno
import shutil
import zipfile
import tempfile

from xml.dom import minidom


KODI_REPOSITORY = 'repository.j0rdyz65'


def main():
    tools_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__))))
    output_path = tools_path

    os.chdir(os.path.abspath(os.path.join(tools_path, os.pardir)))

    repositoryxml_source = None
    if os.path.isdir(KODI_REPOSITORY):
        try:
            doc = minidom.parse(os.path.join(KODI_REPOSITORY, 'addon.xml'))
            for ext in doc.getElementsByTagName('extension'):
                if ext.getAttribute('point') == u'xbmc.addon.repository':
                    repositoryxml_source = ext.toxml()
                    break

        except Exception as ex:
            print >> sys.stderr, 'Error parsing %s/addon.xml: %s'%(KODI_REPOSITORY, repr(ex))
    
    addons_dir = os.listdir('.')
    addonsxml_source = u'<?xml version="1.0" encoding="UTF-8"?>\n<addons>\n'

    for addon_dir in addons_dir:
        if addon_dir == KODI_REPOSITORY:
            continue

        addonxml_path = os.path.join(addon_dir, 'addon.xml')
        if not os.path.isfile(addonxml_path):
            continue

        with open(addonxml_path) as fil:
            addonxml_source = fil.read()

        for line in addonxml_source.split('\n'):
            if line and line.find('<?xml') < 0:
                addonsxml_source += unicode(line+'\n', 'utf-8')

        if repositoryxml_source and '{xbmc_addon_repository_xml}' in addonsxml_source:
            addonrepoxml_source = addonxml_source.format(
                xbmc_addon_repository_xml=repositoryxml_source,
            )
            fil, addonxml_path = tempfile.mkstemp()
            fil.write(addonrepoxml_source)
            fil.close()
            print >> sys.stderr, 'Updated %s/addons.xml with repository info'%addon_dir

        version = generate_zip_file(output_path, addon_dir, addonxml_path)

        for filename in ['changelog.txt', 'icon.png', 'fanart.jpg']:
            filepath = os.path.join(addon_dir, filename)
            if os.path.isfile(filepath):
                repo_filename = 'changelog-%s.txt'%version if filename == 'changelog.txt' else filename
                shutil.copy(filepath, os.path.join(output_path, addon_dir, repo_filename))
                print >> sys.stderr, 'Copied %s to %s'%(filename, repo_filename)

    addonsxml_source += u'</addons>\n'
    addonsxml_source = addonsxml_source.encode('utf-8')

    addonsxml_path = os.path.join(output_path, 'addons.xml')
    with open(addonsxml_path, 'w') as fil:
        fil.write(addonsxml_source)

    print >> sys.stderr, 'Created addons.xml'

    md5hash = md5.new(open(addonsxml_path).read()).hexdigest()
    with open(os.path.join(output_path, 'addons.xml.md5'), 'w') as fil:
        fil.write(md5hash)

    print >> sys.stderr, 'Created addons.xml.md5'

    return 0


def generate_zip_file(output_path, addon_dir, addonxml_path):
    addon_id = None
    addon_version = None
    document = minidom.parse(addonxml_path)
    for parent in document.getElementsByTagName("addon"):
        addon_version = parent.getAttribute("version")
        addon_id = parent.getAttribute("id")

    if not addon_version or not addon_id:
        raise Exception('Malformed %s/addon.xml, missing id and/or version attributes'%addon_dir)


    zip_filename = '%s-%s.zip'%(addon_id, addon_version)
    sys.stderr.write('Generating ZIP file %s...'%zip_filename)
    sys.stderr.flush()

    archive_dir = os.path.join(output_path, addon_id)
    try:
        os.mkdir(archive_dir)
    except OSError as ex:
        if ex.errno == errno.EEXIST:
            pass
        else:
            raise

    zip_path = os.path.join(archive_dir, zip_filename)
    zip_file = zipfile.ZipFile(zip_path, 'w')

    for root, dummy_dirs, files in os.walk(addon_dir):
        for filename in files:
            if '/.git' not in root:
                if filename == 'addon.xml':
                    zip_file.write(addonxml_path, filename)
                else:
                    zip_file.write(os.path.join(root, filename))
                    
    zip_file.close()

    print >> sys.stderr, "DONE"

    return addon_version


if  __name__ == "__main__":
    sys.exit(main())
