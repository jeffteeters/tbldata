from docutils import nodes
from docutils.parsers.rst import Directive

# folloing for function parse_grid_table
import docutils.statemachine
import docutils.parsers.rst.tableparser


from sphinx.locale import _
from sphinx.util.docutils import SphinxDirective


# added going from todo to tbldata

from docutils.parsers.rst import directives
from docutils.statemachine import ViewList
from sphinx.util.nodes import nested_parse_with_titles
import sys
import re
import pprint
pp = pprint.PrettyPrinter(indent=4)
import json


class tbldata(nodes.Admonition, nodes.Element):
    pass


class tblrender(nodes.General, nodes.Element):
    pass


def visit_tbldata_node(self, node):
    self.visit_admonition(node)


def depart_tbldata_node(self, node):
    self.depart_admonition(node)

# utility functions
def get_table_name(d):
    # get table name from directive d
    table_name = d.arguments[0]
    assert len(table_name) > 0, "%s table_name must be present" % d
    assert re.search('\s', table_name) is None, "%s table_name must not contain white space: '%s'" % (d, table_name)
    return table_name

envinfokey = "tbldata_info"
def save_directive_info(env, key, info):
    # save directive info in environment
    global envinfokey
    assert key in ('tbldata', 'tblrender'), "save_directory_info, invalid key: %s" % key
    if not hasattr(env, envinfokey):
        print("*** initializing envinfokey *** ")
        initial_value = {"tbldata":[], "tblrender":[]}
        setattr(env, envinfokey, initial_value)
    # print("saving info in env.%s[%s]" % (envinfokey, key))
    # pp.pprint(info)
    envinfo = getattr(env, envinfokey)
    envinfo[key].append(info)

def retrieve_directive_info(env, key):
    # retrieve info from environemnt 
    global envinfokey
    return env.envinfokey[key]

def make_tds(envinfo):
    # convert envinfo to nested structures that are used to make the tables and links
    #
    # Input (envinfo) contains:
    #
    # {'tbldata': [<ddi1>, <ddi2>, ...], 'tblrender': [ <rdi1>, <rdi2> ...]}
    # <ddi> ("data directive info") == { "docname": self.env.docname, "lineno": self.lineno, "table_name":table_name,
    #        "valrefs":valrefs, "target":target_node}  --- removed: "tbldata_node": tbldata_node.deepcopy() }
    #
    # <rdi> ("render directive info") == {"docname": self.env.docname, "table_name":table_name, "rows":rows, "cols":cols,
    #         "target": target_node}  --- removed:  "tblrender_node": tblrender_node.deepcopy()}
    #
    # Output (tds) - table data sorted, contains:
    #
    # { "tbldata":  # information from each tbldata directive, organized by table_name, row, col.
    #               # used when building the table 
    #     { <table_name>: { <row>: { <col>: [ <ddi-a>, <ddi-b> ... ], ... }, ... }, ... }
    #       where each <ddi> is the structure used in envinfo (but now accessable via row and column)
    #
    # { "tblrender":  # information from each tblrender directive, used for making link from tbldata directive node to table
    #     { <table_name>: [ <rdi>, ...], ... }
    #
    def get_tbldata_label(tag, table_name, fdocname, flineno, tri):
        # convert tag to title, label
        # tag is either "title:label", or label
        # if just label, need to find title.
        # do safety check for same title in table row and column
        # tri - table render info (from tds["tblrender"]["table_name"][0])
        if ":" in tag:
            title, label = tag.split(":")
            if title == tri['row_title']:
                if label not in tri['row_labels']:
                    print("ERROR: tbldata for table '%s' in %s line %s references '%s', but '%s' is not a "
                        "valid option for '%s' in "
                        "tblrender defined in file %s line %s" % (table_name, fdocname, flineno, tag, label,
                        title, tri["docname"], tri["lineno"]))
                    sys.exit("Aborting")
            elif title == tri['col_title']:
               if label not in tri['col_labels']:
                    print("ERROR: tbldata for table '%s' in %s line %s references '%s', but '%s' is not a "
                        "valid option for '%s' in "
                        "tblrender defined in file %s line %s" % (table_name, fdocname, flineno, tag, label,
                        title, tri["docname"], tri["lineno"]))
                    sys.exit("Aborting")
            else:
                print("ERROR: tbldata for table '%s' in %s line %s references title '%s' which is not a "
                    "valid title; should be either '%s' or '%s' for"
                    "tblrender defined in file %s line %s" % (table_name, fdocname, flineno, title, tri['row_title'],
                    tri['col_title'], tri["docname"], tri["lineno"]))
                sys.exit("Aborting")
        else:
            label = tag
            inrows = label in tri['row_labels']
            incols = label in tri['col_labels']
            if inrows and incols:
                print("ERROR: tbldata for table '%s' in file %s line %s references '%s', which is ambiguous "
                    "since it could be either a '%s' or '%s' in "
                    "tblrender defined in file %s line %s" % (table_name, fdocname, flineno, label,
                    tri['row_title'], tri['col_title'], tri["docname"], tri["lineno"]))
                sys.exit("Aborting")
            if inrows:
                title = tri['row_title']
            elif incols:
                title = tri['col_title']
            else:
                print("tbldata for table '%s' in %s line %s references '%s' which is not a valid option for '%s' or '%s' "
                    "in tblrender defined in %s line %s" %(table_name, fdocname, flineno, tag, tri['row_title'],
                    tri['col_title'], tri["docname"], tri["lineno"]))
                sys.exit("Aborting")
        return [title, label]

    # start of mainline for function get_tds
    tds = {"tbldata": {}, "tblrender": {} }
    # convert envinfo["tblrender"] to tds["tblrender"]
    for rdi in envinfo["tblrender"]:
        table_name = rdi["table_name"]
        if table_name not in tds["tblrender"]:
            tds["tblrender"][table_name] = []
        tds["tblrender"][table_name].append(rdi)
    # todo: check to make sure if more than one tblrender of the same table, the rows and cols match
    # print("tds before adding tbldata is:")
    # pp.pprint(tds)
    # convert envinfo["tbldata"] to tds["tbldata"]
    # print("starting make tds, envinfo=")
    # pp.pprint(envinfo)
    for ddi in envinfo["tbldata"]:
        table_name = ddi["table_name"]
        docname = ddi["docname"]
        lineno = ddi["lineno"]
        target = ddi["target"]
        valrefs = ddi["valrefs"]
        if table_name not in tds["tblrender"]:
            print("Error: Table '%s' referenced at %s line %s, but is not defined in a tblrender directive" % (
                table_name, docname, lineno))
            sys.exit("Aborting")
        # valrefs has format:
        # <list of: <row, col, val, reference> in JSON format, without outer enclosing []>                                                             
        # example:
        # ["basket", "cat", 234, "Albus-1989"], ["basket", "rat", 298, "Jones-2002"]
        # convert to JSON (add outer []) then decode to get values
        # print("valrefs=%s" % valrefs)
        # valrefs_decoded = json.loads( "[" + valrefs + "]" )
        tri = tds["tblrender"][table_name][0]
        for data_quad in valrefs:
            tag1, tag2, value, reference = data_quad
            title1, label1 = get_tbldata_label(tag1, table_name, docname, lineno, tri)
            title2, label2 = get_tbldata_label(tag2, table_name, docname, lineno, tri)
            if title1 == title2:
                print("Error: tbldata for table '%s', file %s line %s, row and column are both in '%s'.  Entry is:" % (
                    table_name, docname, lineno, title1))
                print("%s, %s, %s, %s" % (tag1, tag2, value, reference))
                sys.exit("Aborting")
            if title1 == tri["row_title"]:
                assert title2 == tri["col_title"]
                row = label1
                col = label2
            else:
                assert title2 == tri["row_title"]
                assert title1 == tri["col_title"]
                row = label2
                col = label1             
            # row, col, value, reference = data_quad
            # make sure table entry exists for referenced table, row, col
            # following should not be needed anymore because of error checking in get_tbldata_label(
            # if row not in tds["tblrender"][table_name][0]["row_labels"]:
            #     print("Error: Row '%s' in table '%s' referenced at %s line %s, but is not "
            #         "included in tblrender directive" % (row, table_name, docname, lineno))
            #     sys.exit("Aborting")
            # if col not in tds["tblrender"][table_name][0]["col_labels"]:
            #     print("Error: Col '%s' in table '%s' referenced at %s line %s, but is not "
            #         "included in tblrender directive" % (col, table_name, docname, lineno))
            #     sys.exit("Aborting")
            # everything is defined in a tblrender directive, add this to tds["tbldata"]
            if table_name not in tds["tbldata"]:
                tds["tbldata"][table_name] = {}
            if row not in tds["tbldata"][table_name]:
                tds["tbldata"][table_name][row] = {}
            if col not in tds["tbldata"][table_name][row]:
                tds["tbldata"][table_name][row][col] = []
            ref_info = {"docname": docname, "lineno": lineno, "target":target, "valref": data_quad}
            tds["tbldata"][table_name][row][col].append(ref_info)
            # tds["tbldata"][table_name][row][col].append(tde)
            # tds["tbldata"][table_name][row][col].append(ddi)
    # print("made tds, envinfo=")
    # pp.pprint(envinfo)
    # print("tds=")
    # pp.pprint(tds)
    return tds

def make_tds_old(envinfo):
    # convert envinfo to nested structures that are used to make the tables and links
    #
    # Input (envinfo) contains:
    #
    # {'tbldata': [<ddi1>, <ddi2>, ...], 'tblrender': [ <rdi1>, <rdi2> ...]}
    # <ddi> ("data directive info") == { "docname": self.env.docname, "lineno": self.lineno, "table_name":table_name,
    #        "valrefs":valrefs, "target":target_node, "tbldata_node": tbldata_node.deepcopy() }
    #
    # <rdi> ("render directive info") == {"docname": self.env.docname, "table_name":table_name, "rows":rows, "cols":cols,
    #         "target": target_node, "tblrender_node": tblrender_node.deepcopy()}
    #
    # Output (tds) - table data sorted, contains:
    #
    # { "tbldata":  # information from each tbldata directive, organized by table_name, row, col.
    #               # used when building the table 
    #     { <table_name>: { <row>: { <col>: [ <tde1>, <tde2> ... ], ... }, ... }, ... }
    #       where each tde (table data entry) is: 
    #          { "value": <value>, "reference": <reference>, "ddi": <entry in envinfo["tbldata"]> }, 
    #
    # { "tblrender":  # information from each tblrender directive, used for making link from tbldata directive node to table
    #     { <table_name>: [ <rdi>, ...], ... }
    #
    tds = {"tbldata": {}, "tblrender": {} }
    # convert envinfo["tbldata"] to tds["tbldata"]
    # print("starting make tds, envinfo=")
    # pp.pprint(envinfo)
    for ddi in envinfo["tbldata"]:
        table_name = ddi["table_name"]
        valrefs = ddi["valrefs"]
        # valrefs has format:
        # <list of: <row, col, val, reference> in JSON format, without outer enclosing []>                                                             
        # example:
        # ["basket", "cat", 234, "Albus-1989"], ["basket", "rat", 298, "Jones-2002"]
        # convert to JSON (add outer []) then decode to get values
        print("valrefs=%s" % valrefs)
        valrefs_decoded = json.loads( "[" + valrefs + "]" )
        for data_quad in valrefs_decoded:
            row, col, value, reference = data_quad
            tde = {"value": value, "reference":reference, "ddi": ddi }
            if table_name not in tds["tbldata"]:
                tds["tbldata"][table_name] = {}
            if row not in tds["tbldata"][table_name]:
                tds["tbldata"][table_name][row] = {}
            if col not in tds["tbldata"][table_name][row]:
                tds["tbldata"][table_name][row][col] = []
            tds["tbldata"][table_name][row][col].append(tde)
    # convert envinfo["tblrender"] to tds["tblrender"]
    for rdi in envinfo["tblrender"]:
        table_name = rdi["table_name"]
        if table_name not in tds["tblrender"]:
            tds["tblrender"][table_name] = []
        tds["tblrender"][table_name].append(rdi)
    return tds


def purge_directive_info(app, env, docname):
    # def purge_tbldata(app, env, docname):
    global envinfokey
    if not hasattr(env, envinfokey):
        return
    envinfo = getattr(env, envinfokey)
    datainfo = [info for info in envinfo['tbldata']
        if info['docname'] != docname]
    renderinfo =[info for info in envinfo['tblrender']
                                if info['docname'] != docname]
    value = {'tbldata': datainfo, 'tblrender': renderinfo}
    setattr(env, envinfokey, value)


def make_target_node(env):
    target_id = 'tbldata-%d' % env.new_serialno("tbldata")
    target_node = nodes.target('','',ids=[target_id])
    return target_node


def render_rst(d, rst):
    # convert restructured text in rst to nodes for output for directive "d"
    # this copied from sphinxcontrib.datatemplates
    #     DataTemplateBase(rst.Directive) run method
    # added by Jeff Teeters
    result = ViewList()
    data_source = d.env.docname
    for line in rst.splitlines():
        result.append(line, data_source)
    node = nodes.section()
    node.document = d.state.document
    nested_parse_with_titles(d.state, result, node)
    return node.children 

def parse_grid_table(text):
    # Clean up the input: get rid of empty lines and strip all leading and                                                                   
    # trailing whitespace.                                                                                                                   
    lines = filter(bool, (line.strip() for line in text.splitlines()))
    parser = docutils.parsers.rst.tableparser.GridTableParser()
    return parser.parse(docutils.statemachine.StringList(list(lines)))

def extract_gridtable_properties(tabledata):
    # get row and column titles and labels
    # Format of tabledata, from:
    # http://code.nabla.net/doc/docutils/api/docutils/parsers/rst/tableparser/docutils.parsers.rst.tableparser.GridTableParser.html
    # The first item is a list containing column widths (colspecs).
    # The second item is a list of head rows, and the third is a list of body rows.
    # Each row contains a list of cells. Each cell is either None (for a cell unused because of another cell’s span),
    # or a tuple. A cell tuple contains four items: the number of extra rows used by the cell in a vertical span
    # (morerows); the number of extra columns used by the cell in a horizontal span (morecols);
    # the line offset of the first line of the cell contents; and the cell contents, a list of lines of text.

    def slt(sl):
        # return text in StringList
        return " ".join(sl).strip()

    colwidths, headrows, bodyrows = tabledata
    num_cols = len(colwidths)
    num_headrows = len(headrows)
    assert num_headrows in (1, 2), "Must be one or two header rows, found: %s" % num_headrows
    if num_headrows == 2:
        head_col_types = ""
        for i in range(num_cols):
            if headrows[0][i] is not None:
                if headrows[1][i] is None:
                    head_col_types += "u"  # upper row only has content
                else:
                    head_col_types += "b"  # both upper and lower rows
            else:
                assert headrows[1][i] is not None, "both upper and lower header rows are None, should not happen"
                head_col_types += "l"  # lower row only has content
        # find index of first non-None in second header row
        ct_offset = next((i for i, v in enumerate(headrows[1]) if v is not None), -1)
        assert head_col_types[0] == "u", "First column of table with two hearder rows must span both columns"
        bc_index = head_col_types.find("b")
        if bc_index == -1:
            sys.exit("Two header rows in table, but no column with a column title (spaning both header rows)")
        if head_col_types[bc_index+1:] != "l"*(num_cols - bc_index - 1):
            sys.exit("Two header rows in table, but columns after column with title"
                " (spanning both header rows) are not all in lower row only.\nhead_col_types=%s, bc_index=%s\n"
                " head_col_types[bc_index+1:]='%s', 'l'*(num_cols - bc_index -1 )='%s'" %
                (head_col_types, bc_index, head_col_types[bc_index+1:], "l"*(num_cols - bc_index)))
        row_title = slt(headrows[0][0][3])
        col_labels = [ slt(headrows[0][i][3]) if head_col_types[i] == 'u'
                                                  else slt(headrows[1][i][3]) for i in range(1, num_cols) ]
        col_title_span_text = slt(headrows[0][bc_index][3])  # e.g. "Target cell"
        col_title_parts = [col_labels[i] for i in range(bc_index - 1)] + [ col_title_span_text ]
        expanded_col_title = " or ".join(col_title_parts)
        col_title = col_title_span_text
        row_labels = [slt(bodyrows[i][0][3]) for i in range (len(bodyrows))]
        # row_map = { row_labels[i]:i for i in range(len(row_labels))}
        # col_map = { col_labels[i]:i for i in range(len(col_labels))}
        print("row_title='%s'" % row_title)
        print("row_labels='%s'" % row_labels)
        print("col_title='%s'" % col_title)
        print("col_labels='%s'" % col_labels)
        print("ct_offset='%s'" % ct_offset)
        # print("row_map=%s" % row_map)
        # print("col_map=%s" % col_map)
        gridtable_properties = { # "tabledata": tabledata,
            "row_title": row_title, "row_labels": row_labels,
            "col_title": col_title, "col_labels": col_labels,
            "expanded_col_title": expanded_col_title,
            "ct_offset": ct_offset }
            # "row_map":row_map, "col_map":col_map
    else:
        sys.exit("Grid table with only one header row not implemented")
    return gridtable_properties


def generate_gridtable_data(di):
    # use directive info (di) to make grid tabledata structure (described in function extract_gridtable_properties)
    # that can be used to build table vi call to render_gridtable
    # This used if table specified by parameters (rows, cols, col_title, ct_offset) and not by
    # an explicit gridtable structure.
        # di - directive info (dictionary of info describing table)
    table_name = di['table_name']
    row_title = di["row_title"]
    row_labels = di["row_labels"]
    col_title = di["col_title"]
    num_cols = len(col_titles) + 1  # plus 1 for row title
    col_labels = di["col_labels"]
    ct_offset = di["ct_offset"]
    colwidths = [1] * num_cols  # generates list like: [1, 1, 1, ... ]
    hrow1 = []
    hrow2 = []
    for i in range(ct_offset):
        if i == 0:
            hrow1.append([1,0,1,[row_title, ]])
        else:
            hrow1.append([1,0,1,[col_labels[i-1], ]])
        hrow2.append(None)
    # add row title
    hrow1.append([0,num_cols-ct_offset-1,1,[col_title, ]])
    hrow2.append([0,0,1, [col_labels[ct_offset,] ]])
    # complete headers
    for i in range(ct_offset, num_cols):
        hrow1.append(None)
        hrow2.append([0,0,1, [col_labels[i],]])
    headrows = [hrow1, hrow2]
    # build body rows
    bodyrows = []
    for row_num in range(len(row_labels)):
        lineno = row_num * 2 + 3
        bodyrow = []
        bodyrow.append([0,0,lineno, [row_labels[i], ]])
        for i in range(1, num_cols):
            bodyrow.append( [0,0,lineno, ["", ]])
        bodyrows.append(bodyrow)
    tabledata = [colwidths, headrows, bodyrows] 
    return tabledata



# folling adapted from:
# https://sourceforge.net/p/docutils/code/HEAD/tree/trunk/docutils/docutils/parsers/rst/states.py#l1786
def build_table(tabledata, tableline, stub_columns=0, widths=None, classes=None):
    colwidths, headrows, bodyrows = tabledata
    table = nodes.table()
    if widths == 'auto':
        table['classes'] += ['colwidths-auto']
    elif widths: # "grid" or list of integers
        table['classes'] += ['colwidths-given']
    if classes is not None:
        table['classes'] += classes.split()
    tgroup = nodes.tgroup(cols=len(colwidths))
    table += tgroup
    for colwidth in colwidths:
        colspec = nodes.colspec(colwidth=colwidth)
        if stub_columns:
            colspec.attributes['stub'] = 1
            stub_columns -= 1
        tgroup += colspec
    if headrows:
        thead = nodes.thead()
        tgroup += thead
        for row in headrows:
            thead += build_table_row(row, tableline)
    tbody = nodes.tbody()
    tgroup += tbody
    for row in bodyrows:
        tbody += build_table_row(row, tableline)
    return [table]

def build_table_row(rowdata, tableline):
    row = nodes.row()
    for cell in rowdata:
        if cell is None:
            continue
        morerows, morecols, offset, cellblock = cell
        attributes = {}
        if morerows:
            attributes['morerows'] = morerows
        if morecols:
            attributes['morecols'] = morecols
        entry = nodes.entry(**attributes)
        row += entry
        if ''.join(cellblock):
            # import pdb; pdb.set_trace()
            entry += nodes.paragraph(text=" ".join(cellblock).strip())
            # self.nested_parse(cellblock, input_offset=tableline+offset, node=entry)
    return row


# class TblrenderDirective(Directive):
class TblrenderDirective(SphinxDirective):
    # tblrender directive specifies a table to render
    # format:
    # .. tblrender: <table_name>
    #    :description: <description of table>
    #    :row_axis_description: <description of row axis>
    #    :col_axis_description: <description of column axis>
    #    :value_description: <description of each value>
    #    :rows: <row axis name, list of rows, in JSON format, but without enclosing [ ]>
    #    :cols: <column axis name, list of columns, in JSON format, but without enclosing [ ]>
    # example:
    #.. tblrender: cell_counts
    #   :rows: "Cell type", "basket", "grannule"
    #   :cols: "species", "cat", "rat"
    required_arguments = 1
    option_spec = {
        'description': directives.unchanged_required,
        'rows': directives.unchanged,
        'cols': directives.unchanged,
        'expanded_col_title': directives.unchanged,
        'ct_offset': directives.unchanged,
        'gridlayout': directives.unchanged,
    }
    def run(self):
        table_name = get_table_name(self)
        description = self.options.get('description')
        rows = self.options.get('rows')
        cols = self.options.get('cols')
        expanded_col_title = self.options.get('expanded_col_title') # e.g.: Cell count or target cell
        if rows is not None or cols is not None:
            assert rows is not None and cols is not None and expanded_col_title is not None, ("If rows or cols"
                " specified, must specify all of: rows, cols, expanded_col_title")
            rows_decoded = json.loads( "[" + rows + "]" )
            row_title = rows_decoded[0]
            row_labels = rows_decoded[1:]
            cols_decoded = json.loads( "[" + cols + "]" )
            col_title = cols_decoded[0]
            col_labels = cols_decoded[1:]
            expanded_col_title = expanded_col_title.strip("'"+ '"' + " ")
            ct_offset = int(self.options.get('ct_offset', 1))  # number of columns to skip before adding col_title header
            ptable_properties = {"row_title":row_title, "row_labels":row_labels,
                "col_title":col_title, "col_labels":col_labels, "expanded_col_title":expanded_col_title,
                "ct_offset": ct_offset}
        else:
            ptable_properties = None
        gridlayout = self.options.get('gridlayout')
        if gridlayout is not None:
            print("found gridlayout:\n%s" % gridlayout)
            grid_tabledata = parse_grid_table(gridlayout)
            print("headrows=")
            pp.pprint(grid_tabledata[1])
            print("bodyrows=")
            pp.pprint(grid_tabledata[2])
            gridtable_properties = extract_gridtable_properties(grid_tabledata)
            tableline = self.lineno  # a guess
            grid_table_rst = build_table(grid_tabledata, tableline, widths="grid", stub_columns=1, classes="tblrender")
        else:
            grid_table_rst = []
            gridtable_properties = None
            grid_tabledata = None
        if gridtable_properties is None and ptable_properties is None:
            sys.exit("Must specify row and col properties or a gridtable or both")
        make_ptable = ptable_properties is not None
        if gridtable_properties is not None:
            if ptable_properties is not None:
                assert gridtable_properties["row_title"] == ptable_properties["row_title"]
                assert gridtable_properties["row_labels"] == ptable_properties["row_labels"]
                assert gridtable_properties["col_title"] == ptable_properties["col_title"]
                assert gridtable_properties["col_labels"] == ptable_properties["col_labels"]
                assert gridtable_properties["ct_offset"] == ptable_properties["ct_offset"]
                assert gridtable_properties["expanded_col_title"] == ptable_properties["expanded_col_title"], (
                    "expanded_col_title in: gridtable='%s', ptable='%s'" % (
                        gridtable_properties["expanded_col_title"], ptable_properties["expanded_col_title"]))        
            table_properties = gridtable_properties
        else:
            table_properties = ptable_properties

        # target_node = make_target_node(self.env)
        tblrender_node = tblrender('')
        # todo: generate rst to specify label:
        label = ".. _table_%s:" % table_name
        rst = "\n" + label + "\n"
        rst_nodes = render_rst(self, rst)
        # add description to rst for table
        desc_rst = render_rst(self, "\n" + description + "\n\n")
        # rst_nodes += desc_rst + grid_table_rst
        rst_nodes += grid_table_rst
#        .. _table_loebner_fig2a:
#    OR patch labels and targets at end.  How to make reference to table.
        directive_info = {"docname": self.env.docname, "table_name":table_name,
             "desc_rst": desc_rst, "lineno": self.lineno,
             **table_properties,
             "grid_tabledata": grid_tabledata,
             "make_ptable": make_ptable
             }
        # save directive_info as attribute of object so is easy to retrieve in replace_tbldata_and_tblrender_nodes
        tblrender_node.directive_info = directive_info
        save_directive_info(self.env, 'tblrender', directive_info)
        # return target_node for later reference from tbldata directive
        # return tblrender_node to be replaced later by content of table
        # return [target_node, tblrender_node]
        nodes = rst_nodes + [tblrender_node]
        # import pdb; pdb.set_trace()
        return nodes


# start scratch code
"""
        title = "Data for table :ref:`%s <table_%s>`" % (table_name, table_name)
        # create a reference
        # newnode = nodes.reference('','')
        # newnode['refdocname'] = "index"
        # newnode['refuri'] = app.builder.get_relative_uri(
        #     fromdocname, "index")
        # newnode['refuri'] += '#' + ddi['target']['refid']
        # innernode = nodes.emphasis(vref, vref)
        # newnode.append(innernode)
#         title_lines = " ""

#    .. |emphasized hyperlink| replace:: *emphasized hyperlink*
#    .. _emphasized hyperlink: http://example.org

#""
        # heading = "Data for table"
        # title_node = nodes.title()
        # heading = "Here is an |emphasized hyperlink|_."
        # tbldata_node += nodes.title(heading, heading)
        # rst = title_lines.splitlines()
        rst = []
        rst.append(".. cssclass:: tbldata-title")
        rst.append("")         
        rst.append(title)
        rst.append("")
        # title_nodes = render_rst(self, "\n".join(rst))
        # title_node += title_nodes
        # tbldata_node += title_node
        test_ref = None

        for valref in valrefs_decoded:
            row, col, val, ref = valref
            if val == '-' and ref == '-':
                # no reference for single dash so don't include :cite: and :footcite:
                rst.append("   row=%s, col=%s, value='%s' ref='%s'" % (row, col, val, ref))
            else:
                rst.append("   row=%s, col=%s, value='%s' :cite:`%s` :footcite:`%s`" % (row, col, val, ref, ref))
                test_ref = ref
            rst.append("")
        rst = "\n".join(rst)
        rst += example_list_table(test_ref)
        # box_node = nodes.admonition(rst)
        # tbldata_node += nodes.title(_('Data for table'), _('Data for table'))
        # tbldata_node += nodes.title(_(''), _(''))
        rst_nodes = render_rst(self, rst)
"""
# end scratch code


def example_list_table(test_ref):
    source_rst = """

.. list-table:: List tables can have captions like this one.
    :widths: 10 5 10 50
    :header-rows: 1
    :stub-columns: 1

    * - List table
      - Header 1
      - Header 2
      - Header 3 long. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nam sit amet mauris arcu.
    * - Stub Row 1
      - Row 1
      - Column 2
      - Column 3 long. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nam sit amet mauris arcu.
    * - Stub Row 2
      - Row 2
      - Column 2
      - Column 3 long. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nam sit amet mauris arcu.
    * - Stub Row 3
      - Row 3
      - Column 2
      - Column 3 long. Lorem ipsum dolor sit amet, :cite:`%s` :footcite:`%s`.
""" % (test_ref, test_ref)
    return source_rst

def example_grid_table():
    source_rst = """
Test grid table.

+------------------------+----------------------------------+
|                        |               To Cell            |
+------------------------+------------+----------+----------+
| Header row, column 1   | Header 2   | Header 3 | Header 4 |
| (header rows optional) |            |          |          |
+========================+============+==========+==========+
| body row 1, column 1   | column 2   | column 3 | column 4 |
+------------------------+------------+----------+----------+
| body row 2             | ...        | ...      |          |
+------------------------+------------+----------+----------+
"""
    return source_rst


# def make_grid_table_rst():
#     import docutils
#     # from: https://www.generic-mapping-tools.org/sphinx_gmt/v0.1.1/_modules/docutils/parsers/rst.html
#     parser = docutils.parsers.rst.Parser()
#     input = example_grid_table()
#     # from http://code.nabla.net/doc/docutils/api/docutils/utils/docutils.utils.new_document.html
#     settings = docutils.frontend.OptionParser(
#     components=(docutils.parsers.rst.Parser,)
#     ).get_default_values()

# 3. Create a new empty `docutils.nodes.document` tree::

#        document = docutils.utils.new_document(source, settings)

#    See `docutils.utils.new_document()` for parameter details.

# 4. Run the parser, populating the document tree::

#        parser.parse(input, document)

class TbldataDirective(SphinxDirective):
    # tbldata directive specifies data to be included in a table, and also to be shown where the directive is
    # located (making a partial table).  Example format is:
    # .. tbldata: <table_name>
    #
    #    From Cell   |   To Cell  |  Value   |  Reference
    #    basket      |   # cells  |  367     |  Albus-1989
    #    basket      |   perkinje |  45,47   |  Loebner-1963
    #
    # .. tbldata: cell_counts
    #
    #    Cell Type   |   Species  |  Value   |  Reference
    #    Basket      |   Cat      |  234     |  Albus-1989
    #    Basket      |   Rat      |  298     |  Jones-2002
    #
    #
    # Previous style:
    #    :valrefs: <list of: <row, col, val, reference> in JSON format, without outer enclosing []>
    # example:
    # .. tbldata: cell_counts
    #    :valrefs: ["basket", "cat", 234, "Albus-1989"], ["basket", "rat", 298, "Jones-2002"]
    required_arguments = 1
    option_spec = {
        'valrefs': directives.unchanged_required
    }
    # this enables content in the directive
    # include content as comment?
    has_content = True
    def run(self):
        table_name = get_table_name(self)
        target_node = make_target_node(self.env)
        tbldata_node = tbldata()
        # valrefs = self.options.get('valrefs')
        content = self.content
        if len(content) == 0:
            msg = "No data provided for table %s" % table_name
            msg = nodes.Text(msg, msg)
            tbldata_node += msg
            return [ target_node, tbldata_node ]
        # print("content=%s" % content)
        input_rows = content  # .splitlines() # is already split
        header = [x.strip() for x in input_rows[0].split("|")]
        assert len(header) == 4
        assert len(header[0]) > 0
        assert len(header[1]) > 0
        assert ":" not in header[0]
        assert ":" not in header[1]
        assert header[2] == "Value"
        assert header[3] == "Reference"
        valrefs_decoded = []
        table_rst = """
.. list-table:: List tables can have captions like this one.
   :widths: 10 10 10 10
   :header-rows: 1
   :stub-columns: 0

   * - %s
     - %s
     - Value
     - Reference
""" % (header[0], header[1])
        for input_row in input_rows[1:]:
            elements = [x.strip() for x in input_row.split("|")]
            assert len(elements) == 4
            assert ":" not in elements[0]
            assert ":" not in elements[1]
            assert len(elements[0]) > 0
            assert len(elements[1]) > 0
            assert len(elements[2]) > 0
            assert len(elements[3]) > 0
            valrefs = [ header[0] + ":" + elements[0], header[1] + ":" + elements[1], elements[2], elements[3]]
            valrefs_decoded.append(valrefs)
            if elements[2] == "-" and elements[3] == "-":
                # no value or reference
                rst_ref = "-"
            else:
                rst_ref = ":cite:`%s` :footcite:`%s`" % (elements[3], elements[3])
            table_rst += "   * - %s\n     - %s\n     - %s\n     - %s\n" % (
                elements[0], elements[1], elements[2], rst_ref)
        # print("content=%s" % content)
        # valrefs_decoded = json.loads( "[" + valrefs + "]" )
        # target_node = make_target_node(self.env)
        # box = nodes.block_quote()
        # box = nodes.paragraph()
        # prefix_message = "Data for table "
        # prefix_node = nodes.paragraph(prefix_message, prefix_message)
        # generate info to display at directive location using rst so can include citation that uses sphinxbibtex extension, e.g. ":cite:
        # rst = "Data for *%s*\n\n%s\n\nSee :cite:`Albus-1989` for details." % (table_name, valrefs)
        # tbldata_node = tbldata()
        title = "Data for table :ref:`%s <table_%s>`" % (table_name, table_name)
        rst = []
        rst.append(".. cssclass:: tbldata-title")
        rst.append("")         
        rst.append(title)
        rst.append("")
        rst = "\n".join(rst) + table_rst
        rst_nodes = render_rst(self, rst)
        # tbldata_node += rst_nodes
        # rst_nodes = render_rst(self, rst)
        # tbldata_node = tbldata('')
        directive_info = { "docname": self.env.docname, "lineno": self.lineno, "table_name":table_name,
            "valrefs":valrefs_decoded, "target":target_node} #  "tbldata_node": tbldata_node.deepcopy()
        # save directive_info as attribute of object so is easy to retrieve in replace_tbldata_and_tblrender_nodes
        tbldata_node.directive_info = directive_info
        # print("after saving directive info, tbldata node has:")
        # pp.pprint(dir(tbldata_node))
        save_directive_info(self.env, 'tbldata', directive_info)
        print("saved directive_info to tbldata_node id = %s" % id(tbldata_node))
        output_nodes = [target_node, tbldata_node, ] + rst_nodes
        return output_nodes
        # old code
        tbldata_node += target_node
        tbldata_node += rst_nodes
        # print("tbldata_node: %s" % tbldata_node)
        # di = tbldata_node.directive_info
        # pp.pprint(di)

        # box += prefix_node + tbldata_node + rst_nodes
        # return [ target_node, tbldata_node ]
        return [ tbldata_node, ]



class TbldataDirective_old(SphinxDirective):
    # tbldata directive specifies data to be included in a table, and also to be shown where the directive is
    # format:
    # .. tbldata: <table_name>
    #    :valrefs: <list of: <row, col, val, reference> in JSON format, without outer enclosing []>
    # example:
    # .. tbldata: cell_counts
    #    :valrefs: ["basket", "cat", 234, "Albus-1989"], ["basket", "rat", 298, "Jones-2002"]
    required_arguments = 1
    option_spec = {
        'valrefs': directives.unchanged_required
    }
    # this enables content in the directive
    # include content as comment?
    has_content = True


    # Data for table :ref:`num_cells <table_num_cells>`
    # row: cat, col: basket, value: 89 :cite:`MarrD-1969` :footcite:`MarrD-1969`
    # row: human, col: basket, value: 878 :cite:`VanEssenDC-2002` :footcite:`VanEssenDC-2002`


    def run(self):
        table_name = get_table_name(self)
        valrefs = self.options.get('valrefs')
        content = self.content
        print("content=%s" % content)
        valrefs_decoded = json.loads( "[" + valrefs + "]" )
        target_node = make_target_node(self.env)
        # box = nodes.block_quote()
        # box = nodes.paragraph()
        # prefix_message = "Data for table "
        # prefix_node = nodes.paragraph(prefix_message, prefix_message)
        # generate info to display at directive location using rst so can include citation that uses sphinxbibtex extension, e.g. ":cite:
        # rst = "Data for *%s*\n\n%s\n\nSee :cite:`Albus-1989` for details." % (table_name, valrefs)
        tbldata_node = tbldata()
        title = "Data for table :ref:`%s <table_%s>`" % (table_name, table_name)
        # create a reference
        # newnode = nodes.reference('','')
        # newnode['refdocname'] = "index"
        # newnode['refuri'] = app.builder.get_relative_uri(
        #     fromdocname, "index")
        # newnode['refuri'] += '#' + ddi['target']['refid']
        # innernode = nodes.emphasis(vref, vref)
        # newnode.append(innernode)
#         title_lines = """

#    .. |emphasized hyperlink| replace:: *emphasized hyperlink*
#    .. _emphasized hyperlink: http://example.org

# """
        # heading = "Data for table"
        # title_node = nodes.title()
        # heading = "Here is an |emphasized hyperlink|_."
        # tbldata_node += nodes.title(heading, heading)
        # rst = title_lines.splitlines()
        rst = []
        rst.append(".. cssclass:: tbldata-title")
        rst.append("")         
        rst.append(title)
        rst.append("")
        # title_nodes = render_rst(self, "\n".join(rst))
        # title_node += title_nodes
        # tbldata_node += title_node
        test_ref = None

        for valref in valrefs_decoded:
            row, col, val, ref = valref
            if val == '-' and ref == '-':
                # no reference for single dash so don't include :cite: and :footcite:
                rst.append("   row=%s, col=%s, value='%s' ref='%s'" % (row, col, val, ref))
            else:
                rst.append("   row=%s, col=%s, value='%s' :cite:`%s` :footcite:`%s`" % (row, col, val, ref, ref))
                test_ref = ref
            rst.append("")
        rst = "\n".join(rst)
        rst += example_list_table(test_ref)
        # box_node = nodes.admonition(rst)
        # tbldata_node += nodes.title(_('Data for table'), _('Data for table'))
        # tbldata_node += nodes.title(_(''), _(''))
        rst_nodes = render_rst(self, rst)
        tbldata_node += rst_nodes
        # rst_nodes = render_rst(self, rst)
        # tbldata_node = tbldata('')
        directive_info = { "docname": self.env.docname, "lineno": self.lineno, "table_name":table_name,
            "valrefs":valrefs_decoded, "target":target_node} #  "tbldata_node": tbldata_node.deepcopy()
        # save directive_info as attribute of object so is easy to retrieve in replace_tbldata_and_tblrender_nodes
        tbldata_node.directive_info = directive_info
        save_directive_info(self.env, 'tbldata', directive_info)
        # box += prefix_node + tbldata_node + rst_nodes
        return [ target_node, tbldata_node ]

        # return [target_node, prefix_node, tbldata_node] + rst_nodes
        # print("in TbldataDirective run, table_name = '%s', valrefs='%s'" % (table_name, valrefs))
        # rst = "Table: *%s*\n\nvalrefs: %s :ref:`stellate`" % (table_name, valrefs)
        ## tbldata_node = tbldata('\n'.join(self.content) + " :ref:`stellate`")
        # tbldata_node = tbldata(rst)
        # tbldata_node += nodes.title(_('Tbldata'), _('Tbldata'))
        # not sure what the following line does, is this needed?
        # self.state.nested_parse(self.content, self.content_offset, tbldata_node)
        # return target_node for later reference from tblrender entries
        # return tbldata_node to be replaced later by link to table
        # return [target_node, tbldata_node] + rst_nodes


# no longer used
# def purge_tbldata(app, env, docname):
#     global 
#     if not hasattr(env, 'tbldata_all_tbldata'):
#         return
#     env.tbldata_all_tbldata = [tbldata for tbldata in env.tbldata_all_tbldata
#                           if tbldata['docname'] != docname]

def make_docutils_table(header, colwidths, data, hasLinks=False,
    col_title=None, ct_offset=1, tableName=None, descriptionRst=None):
    # col_title on top row above column labels, e.g. col_title = "Target cell", col_labels=["basket", "grannule", ...]
    # hasLinks set True if nodes made before call
    # from:
    # https://agateau.com/2015/docutils-snippets/
    # header = ('Product', 'Unit Price', 'Quantity', 'Price')
    #   colwidths = (2, 1, 1, 1)
    #    data = [
    #        ('Coffee', '2', '2', '4'),
    #        ('Orange Juice', '3', '1', '3'),
    #        ('Croissant', '1.5', '2', '3'),
    #    ]
    # tableName is added to table top
    # col_title is added to top row and spans all columns except first
    # descriptionRst is added before table body
    table = nodes.table()

    numcols = len(header)
    tgroup = nodes.tgroup(cols=numcols)
    table += tgroup
    for colwidth in colwidths:
        tgroup += nodes.colspec(colwidth=colwidth)
    thead = nodes.thead()
    tgroup += thead
    # include abscissaLabel header if present (spans columns 2-end, describes those columns.  eg. "To cell")
    if col_title is not None:
        row = nodes.row()
        # first ct_offset cells (entry) have no label
        for i in range(ct_offset):
            entry = nodes.entry()
            row += entry
        # cell after ct_offset spans all the others and has text
        entry = nodes.entry(morecols=(numcols - ct_offset - 1))
        row += entry
        entry += nodes.paragraph(text=col_title)
        thead += row
    # normal header
    thead += create_table_row(header, hasLinks)

    tbody = nodes.tbody()
    tgroup += tbody
    for data_row in data:
        tbody += create_table_row(data_row, hasLinks)
    return table

def create_table_row(row_cells, hasLinks):
    row = nodes.row()
    for cell in row_cells:
        entry = nodes.entry()
        row += entry
        if hasLinks:
            try:
                entry += cell
            except:
                print("failed entry += cell")
                import pdb; pdb.set_trace()
        else:
            entry += nodes.paragraph(text=cell)
    return row

def make_docutils_test_table():
    header = ('Product', 'Unit Price', 'Quantity', 'Price')
    colwidths = (2, 1, 1, 1)
    data = [
        ('Coffee', '2', '2', '4'),
        ('Orange Juice', '3', '1', '3'),
        ('Croissant', '1.5', '2', '3'),
    ]
    table = make_docutils_table(header, colwidths, data)
    return table

def format_table_data(tds, app, fromdocname):
    # format data provided in tbldata directives into nodes that can be inserted into tables
    # (specified by the tblrender directives)
    # Returns dictionary ftd (formatted table data):
    # ftd[table_name][row][col] = <formatted data>
    ftd = {}
    for table_name in tds["tbldata"]:
        for row in tds["tbldata"][table_name]:
            for col in tds["tbldata"][table_name][row]:
                ddis = tds["tbldata"][table_name][row][col]
                para = nodes.paragraph()
                first_node = True
                for ddi in ddis:
                    target = ddi["target"]
                    valref = ddi["valref"]
                    vrow, vcol, vval, vref = valref
                    # check for "-" in both value and vref.  If found, just display '-' without a link to a target
                    # this is used to allow including dashes to indicate there can be no value for this table cell
                    if vval == '-' and vref == '-':
                        newnode = nodes.Text('-', '-')
                    else:
                        # create a reference
                        newnode = nodes.reference('','')
                        newnode['refdocname'] = ddi['docname']
                        newnode['refuri'] = app.builder.get_relative_uri(
                            fromdocname, ddi['docname'])
                        newnode['refuri'] += '#' + ddi['target']['refid']
                        # innernode = nodes.emphasis(vref, vref)
                        innernode = nodes.emphasis(vval, vval)
                        newnode.append(innernode)
                    # seperator = "; " if not first_node else ""
                    if not first_node:
                        seperator = "; "
                        para += nodes.Text(seperator, seperator)
                    first_node = False
                    # val_str = "%s%s " % (seperator, vval)
                    # para += nodes.Text(val_str, val_str)
                    para += newnode
                # save para in ftd
                if table_name not in ftd:
                    ftd[table_name] = {}
                if row not in ftd[table_name]:
                    ftd[table_name][row] = {}
                ftd[table_name][row][col] = para
    return ftd

# def generate_gridtable(table_name, tds, gridtable_properties, fromdocname):
#     # gridtable_properties = { "tabledata": tabledata,
#     # "row_title": row_title, "row_labels": row_labels,
#     # "col_title": col_title, "col_labels": col_labels,
#     # "row_map":row_map, "col_map":col_map}
#     if table_name not in tds["tbldata"]:
#         sys.exit("No data provided for gridtable %s" % table_name)
#     row_map = gridtable_properties['row_map']
#     col_map = gridtable_properties['col_map']
#     tabledata = gridtable_properties['tabledata']
#     colwidths, headrows, bodyrows = tabledata
#     gridtable_data = {}
#     for row in tds["tbldata"][table_name]:
#         assert row in row_map, "Row '%s' specified in data table not present in gridtable '%s'" % (row, table_name)
#         for col in tds["tbldata"][table_name][row]:
#             assert col in col_map, "Col '%s' specified in data table not present in gridtable '%s'" % (col, table_name)
#             ddis = tds["tbldata"][table_name][row][col]
#             para = nodes.paragraph()
#             first_node = True
#             for ddi in ddis:
#                 target = ddi["target"]
#                 valref = ddi["valref"]
#                 vrow, vcol, vval, vref = valref
#                 # check for "-" in both value and vref.  If found, just display '-' without a link to a target
#                 # this is used to allow including dashes to indicate there can be no value for this table cell
#                 if vval == '-' and vref == '-':
#                     newnode = nodes.Text('-', '-')
#                 else:
#                     # create a reference
#                     newnode = nodes.reference('','')
#                     newnode['refdocname'] = ddi['docname']
#                     newnode['refuri'] = app.builder.get_relative_uri(
#                         fromdocname, ddi['docname'])
#                     newnode['refuri'] += '#' + ddi['target']['refid']
#                     # innernode = nodes.emphasis(vref, vref)
#                     innernode = nodes.emphasis(vval, vval)
#                     newnode.append(innernode)
#                 # seperator = "; " if not first_node else ""
#                 if not first_node:
#                     seperator = "; "
#                     para += nodes.Text(seperator, seperator)
#                 first_node = False
#                 # val_str = "%s%s " % (seperator, vval)
#                 # para += nodes.Text(val_str, val_str)
#                 para += newnode
#             # save para in gridtable_data
#             if row not in gridtable_data:
#                 gridtable_data[row] = {}
#             gridtable_data[row][col] = para


def render_ptable(di, ftd):
    # di - directive info (dictionary of info describing table)
    table_name = di['table_name']
    row_title = di["row_title"]
    row_labels = di["row_labels"]
    col_title = di["col_title"]
    col_labels = di["col_labels"]
    tabledata = []
    for row in row_labels:
        # rowdata = [nodes.paragraph(text=row), ]
        rowdata = [nodes.strong(text=row), ]
        for col in col_labels:
            if (table_name in ftd
                and row in ftd[table_name]
                and col in ftd[table_name][row]):
                para = ftd[table_name][row][col]
            else:
                # no data for this cell
                para = nodes.paragraph()
                empty_flag = " "  # space to indicate empty contents
                para += nodes.Text(empty_flag, empty_flag)
            rowdata.append(para)
        tabledata.append(rowdata)
    # colwidths = [1 for i in len(col_labels)]  # make all colwidts 1 for now
    header = [row_title] + col_labels
    colwidths = [1] * len(header)  # generates list like: [1, 1, 1, ... ]
    header_nodes = [nodes.paragraph(text=cell) for cell in header]
    table = make_docutils_table(header_nodes, colwidths, tabledata, hasLinks=True, col_title=col_title, ct_offset=2)
    return table


def render_gridtable(di, ftd):
    # di - directive info (dictionary of info describing table)
    grid_tabledata = di["grid_tabledata"]
    print("grid_tabledata=")
    pp.pprint(grid_tabledata)
    table_name = di['table_name']
    row_labels = di["row_labels"]
    col_labels = di["col_labels"]
    row_map = { i:row_labels[i] for i in range(len(row_labels))}
    col_map = { i:col_labels[i] for i in range(len(col_labels))}
    tableline = di["lineno"]  # not currently used, but was a parameter to original function below
    grid_table_rst = render_gridtable_rst(grid_tabledata, tableline,
        widths="grid", stub_columns=1, table_name=table_name, # classes="tblrender",
        row_map=row_map, col_map=col_map, ftd=ftd)
    return grid_table_rst

# folling adapted from:
# https://sourceforge.net/p/docutils/code/HEAD/tree/trunk/docutils/docutils/parsers/rst/states.py#l1786
def render_gridtable_rst(tabledata, tableline, stub_columns=0, widths=None, classes=None,
    table_name=None, row_map=None, col_map=None, ftd=None):
    colwidths, headrows, bodyrows = tabledata
    table = nodes.table()
    if widths == 'auto':
        table['classes'] += ['colwidths-auto']
    elif widths: # "grid" or list of integers
        table['classes'] += ['colwidths-given']
    if classes is not None:
        table['classes'] += classes.split()
    tgroup = nodes.tgroup(cols=len(colwidths))
    table += tgroup
    for colwidth in colwidths:
        colspec = nodes.colspec(colwidth=colwidth)
        if stub_columns:
            colspec.attributes['stub'] = 1
            stub_columns -= 1
        tgroup += colspec
    if headrows:
        thead = nodes.thead()
        tgroup += thead
        for row in headrows:
            thead += build_table_row(row, tableline)
    tbody = nodes.tbody()
    tgroup += tbody
    for row_num in range(len(bodyrows)):
        rowdata = bodyrows[row_num]
        tbody += build_gridtable_row(rowdata, tableline, table_name=table_name,
            row_num=row_num, row_map=row_map, col_map=col_map, ftd=ftd)
    return table

def build_gridtable_row(rowdata, tableline, table_name=None, row_num=None, row_map=None, col_map=None, ftd=None):
    row = nodes.row()
    for cell_num in range(len(rowdata)):
        cell = rowdata[cell_num]
        if cell is None:
            continue
        morerows, morecols, offset, cellblock = cell
        attributes = {}
        if morerows:
            attributes['morerows'] = morerows
        if morecols:
            attributes['morecols'] = morecols
        entry = nodes.entry(**attributes)
        row += entry
        try:
            if ''.join(cellblock):
                # import pdb; pdb.set_trace()
                entry += nodes.paragraph(text=" ".join(cellblock).strip())
                # self.nested_parse(cellblock, input_offset=tableline+offset, node=entry)
            elif (ftd is not None and table_name in ftd and row_map[row_num] in ftd[table_name] and
                col_map[cell_num-1] in ftd[table_name][row_map[row_num]]):
                # have data for this cell
                entry += ftd[table_name][row_map[row_num]][col_map[cell_num-1]]
        except KeyError as err:
            print("Key error: {0}".format(err))
            print("row_num=%s, row_map=%s" % (row_num, row_map))
            print("cell_num=%s, col_map=%s" % (cell_num, col_map))
            print("table_name=%s, ftd[table_name]=" % table_name)
            pp.pprint(ftd[table_name])
            sys.exit("aborting")
    return row



def replace_tbldata_and_tblrender_nodes(app, doctree, fromdocname):
    # Does the following:
    #
    # * Replace all tblrender nodes with a table of the data with values in the table
    #   linking to the tbldata directive where the values and references were specified.
    #
    # * Modify each tbldata node with a link to the table generated containing the data.
    #   If the table appears in more than one location, for now, just pick the first location

    global envinfokey
    # print("starting replace_tbldata_and_tblrender_nodes, docname='%s'" % fromdocname)
    env = app.builder.env
    tds = make_tds(getattr(env, envinfokey))
    ftd = format_table_data(tds, app, fromdocname)
    # print("tds['tbldata']=")
    # pp.pprint(tds['tbldata'])
    # import pdb; pdb.set_trace()
    # tds has format:
    # {
    #   "tbldata":  # information from each tbldata directive, organized by table_name, row, col.
    #               # used when building the table 
    #     { <table_name>: { <row>: { <col>: [ <tde1>, <tde2> ... ], ... }, ... }, ... }
    #       where each tde (table data entry) is: 
    #          { "value": <value>, "reference": <reference>, "ddi": <ddi> }, 
    #
    #   "tblrender":  # information from each tblrender directive, used for making link from tbldata directive node to table
    #     { <table_name>: [ <rdi>, ...], ... }
    # }
    # where:
    #
    # <ddi> ("data directive info") == { "docname": self.env.docname, "lineno": self.lineno, "table_name":table_name,
    #        "valrefs":valrefs, "target":target_node, "tbldata_node": tbldata_node.deepcopy() }
    #
    # <rdi> ("render directive info") == {"docname": self.env.docname, "table_name":table_name, "rows":rows, "cols":cols,
    #         "target": target_node, "tblrender_node": tblrender_node.deepcopy()}

    # print("visiting tblrender nodes")

    # insert description into tbldata tables
    # temporary, try to get directive info for tbldata
    for node in doctree.traverse(tblrender):
        di = node.directive_info
        # print ("visiting node, source=%s" % node.source)
        # print ("directive_info=%s" % di)
        # {'docname': 'index', 'table_name': 'num_cells', 'rows': '"Cell type", stellate, grannule',
        # 'cols': 'Species, cat human', 'target': <target: >}
        # directive_info = {"docname": self.env.docname, "table_name":table_name,
        #      "desc_rst": desc_rst, "lineno": self.lineno,
        #      **table_properties,
        #      "grid_tabledata": grid_tabledata,
        #      "make_ptable": make_ptable
        # }
        print("made it to body of replace_tbldata_and_tblrender_nodes")
        # sect = nodes.section()
        node_lst = []  # node list
        para1 = nodes.paragraph()
        msg = "tblrender tables go here"
        para1 += nodes.Text(msg, msg)
        node_lst.append(para1)
        if di["make_ptable"]:
            para2 = nodes.paragraph()
            msg = "ptable goes here"
            para2 += nodes.Text(msg, msg)
            node_lst.append(para2)
            ptable = render_ptable(di, ftd)
            node_lst.append(ptable)
        if di["grid_tabledata"] is not None:
            para3 = nodes.paragraph()
            msg = "gridtable goes here"
            para3 += nodes.Text(msg, msg)
            node_lst.append(para3)
            gridtable = render_gridtable(di, ftd)
            node_lst.append(gridtable)
        print("in replace_tbldata_and_tblrender_nodes, about to replace_self")
        # import pdb; pdb.set_trace()
        node.replace_self(node_lst)
        print("in replace_tbldata_and_tblrender_nodes, just replaced self")
    return

        # scratch code below
    for i in range(10):
        table_name = di['table_name']
        row_title = di["row_title"]
        row_labels = di["row_labels"]
        col_title = di["col_title"]
        col_labels = di["col_labels"]
        gridtable_properties = di["gridtable_properties"]
        if gridtable_properties is not None:
            gridtable_rst = generate_gridtable(table_name, tds, gridtable_properties, fromdocname)
        else:
            gridtable_rst = []
        # description = di["description"]
        tabledata = []
        for row_num in range(len(row_labels)):
            row = row_labels[row_num]
            # rowdata = [nodes.paragraph(text=row), ]
            rowdata = [nodes.strong(text=row), ]
            for col in col_labels:
                if (table_name in tds["tbldata"]
                    and row in tds["tbldata"][table_name]
                    and col in tds["tbldata"][table_name][row]):
                    # entry = []
                    ddis = tds["tbldata"][table_name][row][col]  # data directive info entries
                    # print("row=%s, col=%s, ddis=" % (row, col))
                    # pp.pprint(ddis)
                    # import pdb; pdb.set_trace()
                    # each "ddi" (below loop) will look like:
                    # {"docname": docname, "lineno": lineno, "target":target, "valref": data_quad}
                    # data_quad format: [<row>, <col>, <value>, <valref>]  - all strings
                    # example: ["grannule", "cat", "35", "JGran1972"]
                    para = nodes.paragraph()
                    first_node = True
                    for ddi in ddis:
                        target = ddi["target"]
                        valref = ddi["valref"]
                        vrow, vcol, vval, vref = valref
                        # if vrow != row:
                        #     print("vrow=%s, vcol=%s" % (vrow, vcol))
                        #     import pdb; pdb.set_trace()
                        # should make this stronger assertion
                        assert vrow.endswith(row)
                        assert vcol.endswith(col)
                        # check for "-" in both value and vref.  If found, just display '-' without a link to a target
                        # this is used to allow including dashes to indicate there can be no value for this table cell
                        if vval == '-' and vref == '-':
                            newnode = nodes.Text('-', '-')
                        else:
                            # create a reference
                            newnode = nodes.reference('','')
                            newnode['refdocname'] = ddi['docname']
                            newnode['refuri'] = app.builder.get_relative_uri(
                                fromdocname, ddi['docname'])
                            newnode['refuri'] += '#' + ddi['target']['refid']
                            # innernode = nodes.emphasis(vref, vref)
                            innernode = nodes.emphasis(vval, vval)
                            newnode.append(innernode)
                        # seperator = "; " if not first_node else ""
                        if not first_node:
                            seperator = "; "
                            para += nodes.Text(seperator, seperator)
                        first_node = False
                        # val_str = "%s%s " % (seperator, vval)
                        # para += nodes.Text(val_str, val_str)
                        para += newnode
                        # entry.append("%s--%s" % (vval, vref))
                    # entry = ", ".join(entry)

                    Comment = """
                    para = nodes.paragraph()
                    first_node = True
                    for ddi in ddis:
                        target = ddi["target"]
                        valref = ddi["valref"]
                        vrow, vcol, vval, vref = valref
                        assert vrow == row
                        assert vcol == col
                        # create a reference
                        newnode = nodes.reference('','')
                        newnode['refdocname'] = ddi['docname']
                        newnode['refuri'] = app.builder.get_relative_uri(
                            fromdocname, ddi['docname'])
                        newnode['refuri'] += '#' + ddi['target']['refid']
                        # innernode = nodes.emphasis(vref, vref)
                        innernode = nodes.emphasis(vval, vval)
                        newnode.append(innernode)
                        # seperator = "; " if not first_node else ""
                        if not first_node:
                            seperator = "; "
                            para += nodes.Text(seperator, seperator)
                        first_node = False
                        # val_str = "%s%s " % (seperator, vval)
                        # para += nodes.Text(val_str, val_str)
                        para += newnode
                        # entry.append("%s--%s" % (vval, vref))
                    # entry = ", ".join(entry)
                    # end Comment """

                else:
                    # entry = ""
                    # print("empty cell found")
                    # import pdb; pdb.set_trace()
                    # sys.exit("Aborting.")
                    para = nodes.paragraph()
                    empty_flag = " "  # space to indicate empty contents
                    para += nodes.Text(empty_flag, empty_flag)
                # rowdata.append(entry)
                rowdata.append(para)
            tabledata.append(rowdata)
        # colwidths = [1 for i in len(col_labels)]  # make all colwidts 1 for now
        header = [row_title] + col_labels
        colwidths = [1] * len(header)  # generates list like: [1, 1, 1, ... ]
        header_nodes = [nodes.paragraph(text=cell) for cell in header]
        table = make_docutils_table(header_nodes, colwidths, tabledata, hasLinks=True, col_title=col_title)
        # grid_rst = make_grid_table_rst()
        node.replace_self(table)
    # insert description into tbldata tables
    for node in doctree.traverse(tbldata):
        try:
            di = node.directive_info
        except:
            print("unable to get tbldata directive info, node id = %s" % id(node))
            return
            # with open("doctree.txt", "w") as fp:
            #     fp.write(doctree.pformat())
            # pp.pprint(node)
            # import pdb; pdb.set_trace()
        print("--**-- found directive_info for node id=%s" % id(node))
        table_name = di['table_name']
        desc_rst = tds['tblrender'][table_name][0]['desc_rst']
        # insert desc_rsts before tables
        node.children[2:2] = desc_rst
    return

        # scratch (old version of code) below
        # multvals = []
        # for row in tds["tbldata"][table_name]:
        #     for col in tds["tbldata"][table_name][row]:
        #         valrefs = tds["tbldata"][table_name][row][col]
        #         entry = "row=%s col=%s valrefs=%s" % (row, col, valrefs)
        #         multvals.append(entry)
        # multvals = "\n".join(multvals)
        # description = "table: %s\nrows: %s\ncols: %s\nvals: %s\n" % (table_name, rows, cols, multvals)
        # para = nodes.paragraph()
        # para += nodes.Text(description, description)
        # test_table = make_docutils_test_table()

        # make_docutils_table(header, colwidths, data)
        # content = [ para, ] + test_table
        # node.replace_self(content)

    print("visiting tbldata nodes")
    for node in doctree.traverse(tbldata):
        di = node.directive_info
        # directive_info = { "docname": self.env.docname, "lineno": self.lineno, "table_name":table_name,
        #     "valrefs":valrefs_decoded, "target":target_node}
        table_name = di["table_name"]
        # <rdi> ("render directive info") == {"docname": self.env.docname, "table_name":table_name, "rows":rows, "cols":cols,
        #         "target": target_node}
        rdi = tds["tblrender"][table_name][0]  # zero to select first table
        # create a reference
        newnode = nodes.reference('','')
        newnode['refdocname'] = rdi['docname']
        newnode['refuri'] = app.builder.get_relative_uri(
            fromdocname, rdi['docname'])
        newnode['refuri'] += '#' + rdi['target']['refid']
        innernode = nodes.emphasis(table_name, table_name)
        newnode.append(innernode)
        para = nodes.paragraph(text="Data for table ")
        para += newnode
        node.replace_self(para)
        return






        # print ("visiting node, source=%s" % node.source)
        # print ("directive_info=%s" % directive_info)
        # import pdb; pdb.set_trace()   

    # print('...done vising tblrender and tbldata nodes....')
    # import pdb; pdb.set_trace()
    return

    print("visiting target nodes")
    for node in doctree.traverse(nodes.target):
        directive_info = node.directive_info
        print ("visiting node, source=%s" % node.source)
        print ("directive_info=%s" % directive_info)
        import pdb; pdb.set_trace()
        # if 'refid' in node and node['refid'].startswith('tbldata-'):
        #     refid = node['refid']
        #     # found target node created by this module, following node should be tblrender or tbldata
        #     # get following node
        #     node_traverse = node.traverse(include_self=False, descend = False, siblings = True)
        #     next_node = node_traverse[0]
        #     if isinstance(next_node, tblrender):
        #         print("Found %s, followed by tblrender" % refid)
        #     elif isinstance(next_node, tbldata):
        #         print("Found %s, followed by tbldata" % refid)
        #     else:
        #         print("Unknown node found after %s, %s" % (refid, type(next_node)))
        #         import pdb; pdb.set_trace()


    for table_name in tds["tblrender"]:
        for rdi in tds["tblrender"][table_name]:
            # for now, just output text having all the information
            tblrender_node = rdi["tblrender_node"]
            rows = rdi["rows"]
            cols = rdi["cols"]
            multvals = []
            for row in tds["tbldata"][table_name]:
                for col in tds["tbldata"][table_name][row]:
                    valrefs = tds["tbldata"][table_name][row]
                    entry = "row=%s col=%s valrefs=%s" % (row, col, valrefs)
                    multvals.append(entry)
            multvals = "\n".join(multvals)
            description = "table: %s\nrows: %s\ncols: %s\nvals: %s\n" % (table_name, rows, cols, multvals)
            para = nodes.paragraph()
            para += nodes.Text(description, description)
            content = [ para, ]
            import pdb; pdb.set_trace()
            tblrender_node.replace_self(content)



def process_tbldata_nodes_old(app, doctree, fromdocname):
    assert false
    if not app.config.tbldata_include_tbldata:
        for node in doctree.traverse(tbldata):
            node.parent.remove(node)

    # Replace all tblrender nodes with a list of the collected tbldata.
    # Augment each tbldata with a backlink to the original location.
    env = app.builder.env

    for node in doctree.traverse(tblrender):
        if not app.config.tbldata_include_tbldata:
            node.replace_self([])
            continue

        content = []

        for tbldata_info in env.tbldata_all_tbldata:
            para = nodes.paragraph()
            filename = env.doc2path(tbldata_info['docname'], base=None)
            description = (
                _('(The original entry is located in %s, line %d and can be found ') %
                (filename, tbldata_info['lineno']))
            para += nodes.Text(description, description)

            # Create a reference
            newnode = nodes.reference('', '')
            innernode = nodes.emphasis(_('here'), _('here'))
            newnode['refdocname'] = tbldata_info['docname']
            newnode['refuri'] = app.builder.get_relative_uri(
                fromdocname, tbldata_info['docname'])
            newnode['refuri'] += '#' + tbldata_info['target']['refid']
            newnode.append(innernode)
            para += newnode
            para += nodes.Text('.)', '.)')

            # Insert into the tblrender
            content.append(tbldata_info['tbldata'])
            content.append(para)

        content = build_test_table()
        node.replace_self(content)

def build_test_table(app, doctree, fromdocname):
    print("in build_test_table")
    rst = """
.. -*- mode: rst -*-


.. list-table:: Table from nested lists
   :header-rows: 1

   - * One
     * Two
     * Three
   - * a
     * b
     * :ref:`stellate`
   - * A
     * B
     * C


For more data see :ref:`stellate` link.
"""
    result = ViewList()
    rendered_template = rst
    data_source = 'data.json'
    # import pdb; pdb.set_trace()
    for line in rendered_template.splitlines():
        result.append(line, data_source)
    node = nodes.section()
    node.document = self.state.document
    nested_parse_with_titles(self.state, result, node)
    return node.children



def setup(app):
    # app.add_config_value('tbldata_include_tbldata', False, 'html')
    print("Starting setup in tbldata.py")

    app.add_node(tblrender)
    app.add_node(tbldata,
                 html=(visit_tbldata_node, depart_tbldata_node),
                 latex=(visit_tbldata_node, depart_tbldata_node),
                 text=(visit_tbldata_node, depart_tbldata_node))

    app.add_directive('tbldata', TbldataDirective)
    app.add_directive('tblrender', TblrenderDirective)
    app.connect('doctree-resolved', replace_tbldata_and_tblrender_nodes)
    app.connect('env-purge-doc', purge_directive_info)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }

