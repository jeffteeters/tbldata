from docutils import nodes
from docutils.parsers.rst import Directive

from sphinx.locale import _
from sphinx.util.docutils import SphinxDirective


# added going from todo to tbldata

from docutils.parsers.rst import directives
from docutils.statemachine import ViewList
from sphinx.util.nodes import nested_parse_with_titles

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
    tbl_name = d.arguments[0]
    assert len(tbl_name) > 0, "%s tbl_name must be present" % d
    assert re.search('\s', tbl_name) is None, "%s tbl_name must not contain white space: '%s'" % (d, tbl_name)
    return tbl_name

envinfokey = "tbldata_info"
def save_directive_info(env, key, info):
    # save directive info in environment
    global envinfokey
    assert key in ('tbldata', 'tblrender'), "save_directory_info, invalid key: %s" % key
    if not hasattr(env, envinfokey):
        print("*** initializing envinfokey *** ")
        initial_value = {"tbldata":[], "tblrender":[]}
        setattr(env, envinfokey, initial_value)
    print("saving info in env.%s[%s]" % (envinfokey, key))
    pp.pprint(info)
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
    # <ddi> ("data directive info") == { "docname": self.env.docname, "lineno": self.lineno, "tbl_name":tbl_name,
    #        "valrefs":valrefs, "target":target_node, "tbldata_node": tbldata_node.deepcopy() }
    #
    # <rdi> ("render directive info") == {"docname": self.env.docname, "tbl_name":tbl_name, "rows":rows, "cols":cols,
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
    print("make tds, envinfo")
    pp.pprint(envinfo)
    for ddi in envinfo["tbldata"]:
        table_name = ddi["tbl_name"]
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
        table_name = rdi["tbl_name"]
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

# class TblrenderDirective(Directive):
class TblrenderDirective(SphinxDirective):
    # tblrender directive specifies a table to render
    # format:
    # .. tblrender: <table_name>
    #    :rows: <row axis name, list of rows, in JSON format, but without enclosing [ ]>
    #    :cols: <column axis name, list of columns, in JSON format, but without enclosing [ ]>
    # example:
    #.. tblrender: cell_counts
    #   :rows: "Cell type", "basket", "grannule"
    #   :cols: "species", "cat", "rat"
    required_arguments = 1
    option_spec = {
        'rows': directives.unchanged_required,
        'cols': directives.unchanged_required,
    }
    def run(self):
        tbl_name = get_table_name(self)
        rows = self.options.get('rows')
        cols = self.options.get('cols')
        target_node = make_target_node(self.env)
        tblrender_node = tblrender('')
        directive_info = {"docname": self.env.docname, "tbl_name":tbl_name, "rows":rows, "cols":cols,
             "target": target_node, "tblrender_node": tblrender_node.deepcopy()}
        save_directive_info(self.env, 'tblrender', directive_info)
        # return target_node for later reference from tbldata directive
        # return tblrender_node to be replaced later by content of table
        return [target_node, tblrender_node] 

class TbldataDirective(SphinxDirective):
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

    def run(self):
        tbl_name = get_table_name(self)
        valrefs = self.options.get('valrefs')
        target_node = make_target_node(self.env)
        tbldata_node = tbldata('')
        directive_info = { "docname": self.env.docname, "lineno": self.lineno, "tbl_name":tbl_name,
            "valrefs":valrefs, "target":target_node, "tbldata_node": tbldata_node.deepcopy()
        }
        save_directive_info(self.env, 'tbldata', directive_info)
        # generate info to display at directive location using rst so can include citation that uses sphinxbibtex extension, e.g. ":cite:
        rst = "Data for *%s*\n\n%s\n\nSee :cite:`Albus-1989` for details." % (tbl_name, valrefs)
        rst_nodes = render_rst(self, rst)
        # print("in TbldataDirective run, tbl_name = '%s', valrefs='%s'" % (tbl_name, valrefs))
        # rst = "Table: *%s*\n\nvalrefs: %s :ref:`stellate`" % (tbl_name, valrefs)
        ## tbldata_node = tbldata('\n'.join(self.content) + " :ref:`stellate`")
        # tbldata_node = tbldata(rst)
        # tbldata_node += nodes.title(_('Tbldata'), _('Tbldata'))
        # not sure what the following line does, is this needed?
        # self.state.nested_parse(self.content, self.content_offset, tbldata_node)
        # return target_node for later reference from tblrender entries
        # return tbldata_node to be replaced later by link to table
        return [target_node, tbldata_node] + rst_nodes


# no longer used
# def purge_tbldata(app, env, docname):
#     global 
#     if not hasattr(env, 'tbldata_all_tbldata'):
#         return
#     env.tbldata_all_tbldata = [tbldata for tbldata in env.tbldata_all_tbldata
#                           if tbldata['docname'] != docname]



def replace_tbldata_and_tblrender_nodes(app, doctree, docname):
    # Does the following:
    #
    # * Replace all tblrender nodes with a table of the data with values in the table
    #   linking to the tbldata directive where the values and references were specified.
    #
    # * Modify each tbldata node with a link to the table generated containing the data.
    #   If the table appears in more than one location, for now, just pick the first location

    global envinfokey
    print("starting replace_tbldata_and_tblrender_nodes, docname='%s'" % docname)
    env = app.builder.env
    tds = make_tds(getattr(env, envinfokey))
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
    # <ddi> ("data directive info") == { "docname": self.env.docname, "lineno": self.lineno, "tbl_name":tbl_name,
    #        "valrefs":valrefs, "target":target_node, "tbldata_node": tbldata_node.deepcopy() }
    #
    # <rdi> ("render directive info") == {"docname": self.env.docname, "tbl_name":tbl_name, "rows":rows, "cols":cols,
    #         "target": target_node, "tblrender_node": tblrender_node.deepcopy()}

    print("visiting target nodes")
    for node in doctree.traverse(nodes.target):
        print ("source=%s" % node.source)
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

    print("visiting tblrender nodes")
    for node in doctree.traverse(tblrender):
        import pdb; pdb.set_trace()

    print("visiting tbldata nodes")
    for node in doctree.traverse(tbldata):
        import pdb; pdb.set_trace()   

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
    import pdb; pdb.set_trace()
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

