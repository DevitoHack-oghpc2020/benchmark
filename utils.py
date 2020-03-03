import json
import sys
from collections import OrderedDict


acoustic_table = """
<div class="table100-head">
    <table>
        <thead>
            <tr class="row100 head">
                <th class="cell100 column1">Username</th>
                <th class="cell100 column2">Time (s)</th>
                <th class="cell100 column3">Perf (Gpts/s)</th>
                <th class="cell100 column4">𝚫 err</th>
            </tr>
        </thead>
    </table>
</div>

<div class="table100-body js-pscroll">
    <table>
        <tbody>
            {0}
        </tbody>
    </table>
</div>
"""


tti_table = """
<div class="table100-head">
    <table>
        <thead>
            <tr class="row100 head">
                <th class="cell100 column1">Username</th>
                <th class="cell100 column2">Time (s)</th>
                <th class="cell100 column3">Perf (Gpts/s)</th>
                <th class="cell100 column4">𝚫 err</th>
            </tr>
        </thead>
    </table>
</div>

<div class="table100-body js-pscroll">
    <table>
        <tbody>
            {0}
        </tbody>
    </table>
</div>
"""

row_acoustic_template = """
    <tr class="row100 body">
        <td class="cell100 column1">{0}</td>
        <td class="cell100 column2">{1}</td>
        <td class="cell100 column3">{2}</td>
        <td class="cell100 column4">{3}</td>
    </tr>
    """

row_tti_template = """
    <tr class="row100 body">
        <td class="cell100 column1">{0}</td>
        <td class="cell100 column2">{1}</td>
        <td class="cell100 column3">{2}</td>
        <td class="cell100 column4">{3}</td>
    </tr>
    """


def json_to_table(data, type):

    if type == 'acoustic':
        table = acoustic_table
    elif type == 'tti':
        table = tti_table

    a = sorted(data.items(), key=lambda x: x[1][type]['time'])
    content = ''

    for row in a:

        user = row[0]
        mapper = data[user][type]

        if type == 'acoustic':
            content = content + row_acoustic_template.format(
                user,
                mapper['time'],
                mapper['perf'],
                'None' if not mapper['err'] else ('(rec = %s ; u = %s)' %
                                                  (str(mapper['err']['rec'][2]),
                                                   str(mapper['err']['u'][2])))
            )
        elif type == 'tti':
            content = content + row_tti_template.format(
                user,
                mapper['time'],
                mapper['perf'],
                'None' if not mapper['err'] else ('(rec = %s ; u = %s ; v = %s)' %
                                                  (str(mapper['err']['rec'][2]),
                                                   str(mapper['err']['u'][2]),
                                                   str(mapper['err']['v'][2]))))

    return table.format(content)


def generate_score_html(data):

    acoustic = json_to_table(data, 'acoustic')
    tti = json_to_table(data, 'tti')

    with open('score_template.html') as file_template:

        template = str(file_template.read())

        template = template.replace("_acoustic_table_", acoustic)
        template = template.replace("_tti_table_", tti)

    output_file = open("DevitoHack-oghpc2020.github.io/index.html", 'w')
    output_file.write(template)
    output_file.close()
