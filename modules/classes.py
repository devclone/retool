import re

from modules.titleutils import get_languages, get_raw_title, remove_languages,\
    remove_regions, remove_tags
from modules.utils import Font

class CloneList:
    """ Returns a formatted clone list """

    def __init__(self, compilations, overrides, conditional_overrides, renames):
        self.compilations = compilations
        self.renames = renames
        self.overrides = overrides
        self.conditional_overrides = conditional_overrides


class Dat:
    """ Returns an object that contains the input dat's details """

    def __init__(self, contents='', name='Unknown', description='Unknown', version='Unknown', author='Unknown', url='Unknown', user_options=[]):
        self.name = name
        self.description = description
        self.version = version
        self.author = author
        self.url = url
        self.contents = contents
        self.user_options = user_options


class DatNode:
    """ Returns an object that contains all of a title's properties """

    def __init__(self, node, region, region_data, user_input, input_dat, REGEX):

        self.full_name = str(node.category.parent['name'])

        metadata = input_dat.metadata

        if self.full_name in metadata:
            self.secondary_name = metadata[self.full_name]['secondary_name']
            self.status = metadata[self.full_name]['status']
            self.online_languages = metadata[self.full_name]['languages']
            self.version = metadata[self.full_name]['version']
            self.disc_type = metadata[self.full_name]['disc_type']
        else:
            self.secondary_name = ''
            self.status = ''
            self.online_languages = ''
            self.version = ''

        self.disc_type_parent = ''

        # Set title with minimal tags, starting with normalizing disc names
        tag_free_name = self.full_name

        for key, value in user_input.tag_strings.disc_rename.items():
            if key in tag_free_name:
                tag_free_name = tag_free_name.replace(key, value)

        # Strip out other tags found in tags.json
        self.tag_free_name = remove_tags(tag_free_name, user_input, REGEX)

        # Set region free, language free title
        if re.search(' \((.*?,){0,} {0,}' + region + '(,.*?){0,}\)', self.full_name) != None:
            self.region_free_name = remove_regions(remove_languages(self.full_name, REGEX.languages), region_data)

            # Now set regionless title with minimal tags
            self.short_name = remove_regions(remove_languages(self.tag_free_name, REGEX.languages), region_data)
        else:
            self.region_free_name = self.full_name
            self.short_name = self.tag_free_name

        self.title_languages = get_languages(self.full_name, REGEX.languages)
        self.group = get_raw_title(self.full_name)

        # Set implied language for the region
        if region != 'Unknown':
            self.implied_language = region_data.implied_language[region]

            self.regions = re.search('\((.*?,){0,} {0,}' + region + '(,.*?){0,}\)', self.full_name)[0][1:-1]

            for another_region in region_data.all:
                if re.search(' \(' + another_region + '(,.*?){0,}\)', self.full_name) != None:
                    self.primary_region = another_region
                    break

            for i, x in enumerate(region_data.all):
                if self.primary_region == x:
                    self.region_priority = i
        else:
            self.implied_language = ''
            self.regions = ''
            self.primary_region = ''
            self.region_priority = 100

        if ',' in self.regions:
            self.secondary_region = self.regions.replace(self.primary_region + ', ', '')
        else:
            self.secondary_region = ''

        self.category = node.category.contents[0]
        self.description = node.description.contents[0]
        self.cloneof = ''
        self.cloneof_group = ''

        # From multiple sources, set the canonical supported languages for the title
        if self.online_languages != '':
            self.languages = self.online_languages
        elif self.online_languages == '' and self.title_languages == '':
            self.languages = self.implied_language
        elif self.online_languages == '' and self.title_languages != '':
            self.languages = self.title_languages

        # Convert the <rom> lines for the current node
        node_roms = node.findChildren('rom', recursive=False)
        roms = []
        for rom in node_roms:
            roms.append(DatNodeRom('rom', rom['crc'], rom['md5'], rom['name'], rom['sha1'], rom['size']))

        self.roms = roms

        if self.full_name not in metadata:
            # Calculate total disc size
            disc_size = 0
            for i, rom in enumerate(self.roms):
                disc_size += int(rom.size)

            # Disc type, defined by maximum CD size in bytes, or if it's a
            # multitrack disc.
            if disc_size <= 999300000 or len(self.roms) > 1:
                self.disc_type = 'CD-ROM/GD-ROM'
            elif disc_size > 9395241000:
                self.disc_type = 'BD-ROM'
            else:
                self.disc_type = 'DVD/BD-ROM'

    def __str__(self):
        ret_str = []


        def format_property(property, string, tabs):
            """ Formats a string properly based on whether a property has a value
            or not """

            none_str = f'{Font.disabled}None{Font.end}'
            if property == '':
                ret_str.append(f'  ├ {string}:{tabs}{none_str}\n')
            else:
                ret_str.append(f'  ├ {string}:{tabs}{property}\n')


        ret_str.append(f'  ○ full_name:\t\t{self.full_name}\n')
        format_property(self.secondary_name, 'secondary_name', '\t')
        ret_str.append(f'  ├ description:\t{self.description}\n')
        ret_str.append(f'  ├ region_free_name:\t{self.region_free_name}\n')
        ret_str.append(f'  ├ tag_free_name:\t{self.tag_free_name}\n')
        ret_str.append(f'  ├ short_name:\t\t{self.short_name}\n')
        ret_str.append(f'  ├ group:\t\t{self.group}\n')
        format_property(self.status, 'status', '\t\t')
        format_property(self.version, 'version', '\t\t')
        ret_str.append(f'  ├ regions:\t\t{self.regions}\n')
        ret_str.append(f'  ├ primary_region:\t{self.primary_region}\n')
        format_property(self.secondary_region, 'secondary_region', '\t')
        ret_str.append(f'  ├ region_priority:\t{str(self.region_priority)}\n')
        format_property(self.title_languages, 'title_languages', '\t')
        format_property(self.implied_language, 'implied_language', '\t')
        format_property(self.online_languages, 'online_languages', '\t')
        format_property(self.languages, 'languages', '\t\t')
        format_property(self.cloneof, 'cloneof', '\t\t')
        format_property(self.cloneof_group, 'cloneof_group', '\t')
        ret_str.append(f'  ├ category:\t\t{self.category}\n')
        format_property(self.disc_type, 'disc_type', '\t\t')
        format_property(self.disc_type_parent, 'disc_type_parent', '\t')
        ret_str.append(f'  └ roms ┐\n')
        for i, rom in enumerate(self.roms):
            if i == len(self.roms) - 1:
                ret_str.append(f'         └ name: {rom.name} | crc: {rom.crc} | md5: {rom.md5} | sha1: {rom.sha1} | size: {rom.size}\n\n')
            else:
                ret_str.append(f'         ├ name: {rom.name} | crc: {rom.crc} | md5: {rom.md5} | sha1: {rom.sha1} | size: {rom.size}\n')

        ret_str = ''.join(ret_str)
        return ret_str


class DatNodeRom:
    """ Returns an object that contains a title's rom properties """

    def __init__(self, rom, crc, md5, name, sha1, size):
        self.crc = crc
        self.md5 = md5
        self.name = name
        self.sha1 = sha1
        self.size = size


class Regex:
    """ Regex constructor """

    def __init__(self, LANGUAGES):
        self.alt = re.compile('\(Alt.*?\)')
        self.covermount = re.compile('\(Covermount\)')
        self.dates = re.compile('\(\d{8}\)')
        self.dates_whitespace = re.compile('\s?\(\d{8}\)\s?')
        self.edc = re.compile('\(EDC\)')
        self.languages = re.compile('( (\((' + LANGUAGES + ')\.*?)(,.*?\)|\)))')
        self.oem = re.compile('\((?:(?!\(|OEM.*?)[\s\S])*OEM.*?\)')
        self.hibaihin = re.compile('\(Hibaihin.*?\)')
        self.rerelease = re.compile('\(Rerelease\)')
        self.revision = re.compile('\(Rev [0-9A-Z].*?\)')
        self.sega_ring_code = re.compile('\(([0-9]{1,2}[A-Z]([ ,].[0-9]{1,2}[A-Z])*|R[E]{,1}[-]{,1}[0-9]{,1})\)')
        self.sega_ring_code_re = re.compile('R[E]{,1}[-]{,1}[0-9]{,1}')
        self.version = re.compile('\(v[0-9].*?\)')
        self.long_version = re.compile('Version [+-]?([0-9]+([.][0-9]*)?|[.][0-9]+).*?[ \)]')


class RegionKeys():
    """ Region keys constructor """

    def __init__(self):
        self.filename = 'internal-config.json'
        self.region_order = 'default_region_order'
        self.languages = 'languages'


class Regions():
    """ Regions constructor """

    def __init__(self):
        self.all = []
        self.region_order = []
        self.implied_language = []
        self.languages_filter = []
        self.languages_long = []
        self.languages_short = []
        self.languages_key = {}

    def __str__(self):
        ret_str = []
        replace_str = ',\n    '

        ret_str.append(
            f'  ○ all:\n    [  \n     '
            f'{str(self.all)[1:-1].replace(",", replace_str)}\n    ]\n')
        ret_str.append(
            f'  ○ region_order:\n    [  \n     '
            f'{str(self.region_order)[1:-1].replace(",", replace_str)}\n    ]\n')
        ret_str.append(
            f'  ○ implied_language:\n    [  \n     '
            f'{str(self.implied_language)[1:-1].replace(",", replace_str)}\n    ]\n')

        ret_str = ''.join(ret_str)

        return ret_str


class Stats():
    """ Stores stats before processing the dat """

    def __init__(self, original_title_count, user_input, input_dat, final_title_count=0):
        def category_count(category):
            """ Gets the category count for the soup object """

            if hasattr(user_input, 'no_' + category.lower()):
                if getattr(user_input, 'no_' + category.lower()) == True:
                    return len(input_dat.soup.find_all('category', string=category))
                else:
                    return 0

        self.original_title_count = original_title_count
        self.final_title_count = final_title_count
        self.applications_count = category_count('Applications')
        self.coverdiscs_count = category_count('Coverdiscs')
        self.demos_count = category_count('Demos')
        self.educational_count = category_count('Educational')
        self.multimedia_count = category_count('Multimedia')
        self.preproduction_count = category_count('Preproduction')

        if user_input.no_unlicensed == True:
            self.unlicensed_count = len(input_dat.soup.find_all('description', string=lambda x: x and '(Unl)' in x))
        else:
            self.unlicensed_count = 0


class TagKeys:
    """ Tag keys constructor """

    def __init__(self):
        self.filename = 'internal-config.json'
        self.demote_editions = 'demote_editions'
        self.disc_rename = 'disc_rename'
        self.ignore = 'ignore_tags'
        self.promote_editions = 'promote_editions'


class Tags:
    """ Tags constructor """

    def __init__(self):
        self.demote_editions = set()
        self.disc_rename = {}
        self.ignore = set()
        self.promote_editions = set()

    def __str__(self):
        ret_str = []
        replace_str = ',\n    '

        ret_str.append(
            f'  ○ demote_editions:\n    [  \n     '
            f'{str(self.demote_editions)[1:-1].replace(",", replace_str)}\n    ]\n')
        ret_str.append(
            f'  ○ disc_rename:\n    {{  \n     '
            f'{str(self.disc_rename)[1:-1].replace(",", replace_str)}\n    }}\n')
        ret_str.append(
            f'  ○ ignore:\n    [  \n     '
            f'{str(self.ignore)[1:-1].replace(",", replace_str)}\n    ]\n')
        ret_str.append(
            f'  ○ promote_editions:\n    [  \n     '
            f'{str(self.promote_editions)[1:-1].replace(",", replace_str)}\n    ]\n')

        ret_str = ''.join(ret_str)

        return ret_str


class Titles:
    """ Tag keys constructor """

    def __init__(self):
        self.all = {}
        self.regions = {}


class UserInput:
    """ Stores user input values, including what types of titles to exclude """

    def __init__(self, input_file_name, output_folder_name,
                 no_demos, no_applications, no_preproduction,
                 no_multimedia, no_educational, no_coverdiscs,
                 no_compilations, no_unlicensed, supersets,
                 filter_languages, legacy, user_options, verbose):
        self.input_file_name = input_file_name
        self.output_folder_name = output_folder_name
        self.no_demos = no_demos
        self.no_applications = no_applications
        self.no_multimedia = no_multimedia
        self.no_preproduction = no_preproduction
        self.no_educational = no_educational
        self.no_coverdiscs = no_coverdiscs
        self.no_compilations = no_compilations
        self.no_unlicensed = no_unlicensed
        self.supersets = supersets
        self.filter_languages = filter_languages
        self.legacy = legacy
        self.user_options = user_options
        self.verbose = verbose