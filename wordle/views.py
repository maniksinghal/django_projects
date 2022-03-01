from django.shortcuts import render
import logging

from wordle.core_logic import initialize_db, process_next_word

GREY = "#AAAAAA"
GREEN = "#00aa00"
ORANGE = "#ffa500"
LIGHT_BLUE = "#add8e6"
WHITE = "#ffffff"

logger = logging.getLogger(__name__)

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(name)-12s %(levelname)-8s %(message)s'
        },
        'file': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'file',
            'filename': '/tmp/debug.log'
        }
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': ['console', 'file']
        }
    }
})


def create_base_dict():
    base_dict = {}

    base_cell_attrs = 'size=1 '
    base_cell_attrs += 'onClick=\"cell_clicked(this);\" title="Please enter alphabets" '
    base_cell_attrs += 'onfocusin="this.select()" '

    base_dict['base_cell_attrs'] = base_cell_attrs

    rows = list()
    for i in range(5):
        row_obj = {}
        row_obj['cells'] = list()
        rows.append(row_obj)
        for j in range(5):
            cell_obj = {}
            cell_obj['name'] = "c%d%d" % (i,j)
            cell_obj['bg_color'] = GREY
            cell_obj['type'] = "text"
            if i > 0:
                # All following rows are read-only
                cell_obj['read_only'] = "readonly"
                cell_obj ['required'] = ""
                cell_obj['type'] = "hidden"
            else:
                cell_obj['read_only'] = ""
                cell_obj ['required'] = "required"
                cell_obj ['bg_color'] = LIGHT_BLUE
            cell_obj['value'] = ""
            cell_obj['hidden_value'] = "N"
            row_obj['cells'].append(cell_obj)

    base_dict['rows'] = rows
    base_dict['focus_cell'] = "c00"
    base_dict['active_row'] = "0"
    base_dict['suggestions'] = "Suggestions shall be listed here"
    return base_dict
    
# Create your views here.
def home(request):
    base_dict = create_base_dict()
    return render(request, 'wordle/base.html', base_dict)

def solve_next(request):
    db = initialize_db()
    base_dict = create_base_dict()
    row_to_edit = None
    suggested_words = None
    suggestions_expected = False
    for row in range(5):
        outcomes = ""
        word = ""
        for col in range(5):
            cell_obj = base_dict['rows'][row]['cells'][col]
            cell = "c%d%d" % (row, col)
            cell_hidden = "%s_hidden" % cell
            cell_value = request.GET.get(cell)
            cell_hidden_value = request.GET.get(cell_hidden)

            if cell_value:
                word += cell_value
                outcomes += cell_hidden_value

            if cell_value or (row_to_edit is not None and row_to_edit != row):
                #Already filled cell, copy back
                cell_obj['value'] = cell_value
                cell_obj['hidden_value'] = cell_hidden_value
                cell_obj['read_only'] = "readonly"
                cell_obj['required'] = ""
                if cell_hidden_value == "N":
                    cell_obj['bg_color'] = GREY
                elif cell_hidden_value == "W":
                    cell_obj['bg_color'] = ORANGE
                else:
                    cell_obj['bg_color'] = GREEN
                
                if cell_value:
                    #Already filled cell
                    cell_obj['type'] = "text"
                else:
                    #Row after the row-to-edit
                    cell_obj['type'] = "hidden"
            else:
                row_to_edit = row
                #Allow user to edit this row
                cell_obj['read_only'] = ""
                cell_obj['required'] = "required"
                cell_obj['bg_color'] = LIGHT_BLUE
                cell_obj['type'] = "text"
                base_dict['active_row'] = row
                #Rest values are base defaults
        
        if word:
            if outcomes == "CCCCC":
                break
            (db, suggested_words) = process_next_word(db, word, outcomes)
            suggestions_expected = True
    if row_to_edit:
        base_dict['focus_cell'] = "c%d0" % row_to_edit
    
    if outcomes == "CCCCC":
        suggestion = "Hurray!!"
    elif not suggestions_expected:
        suggestion = "Suggested words appear here"
    elif suggested_words is None:
        suggestion = "Internal error!!"
    elif len(suggested_words) == 0:
        suggestion = "Ran out of words!!"
    else:
        suggestion = "Try %s" % ",    ".join(suggested_words)
    base_dict['suggestions'] = suggestion
    return render(request, 'wordle/base.html', base_dict)