# coding: utf-8
# /*##########################################################################
#
# Copyright (c) 2004-2016 European Synchrotron Radiation Facility
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# ###########################################################################*/
"""This module provides table widgets handling cut, copy and paste for
multiple cell selections. These actions can be triggered using keyboard
shortcuts or through a context menu (right-click).

:class:`TableView` is a subclass of :class:`QTableView`. The added features
are made available to users after a model is added to the widget, using
:meth:`TableView.setModel`.

:class:`TableWidget` is a subclass of :class:`qt.QTableWidget`, a table view
with a built-in standard data model. The added features are available as soon as
the widget is initialized.

The cut, copy and paste actions are implemented as QActions:

    - :class:`CopySelectedCellsAction` (*Ctrl+C*)
    - :class:`CopyAllCellsAction`
    - :class:`CutSelectedCellsAction` (*Ctrl+X*)
    - :class:`CutAllCellsAction`
    - :class:`PasteCellsAction` (*Ctrl+V*)

The copy actions are enabled by default. The cut and paste actions must be
explicitly enabled, by passing parameters ``cut=True, paste=True`` when
creating the widgets, or later by calling their :meth:`enableCut` and
:meth:`enablePaste` methods.
"""

__authors__ = ["P. Knobel"]
__license__ = "MIT"
__date__ = "26/01/2017"


import sys
from .. import qt


if sys.platform.startswith("win"):
    row_separator = "\r\n"
else:
    row_separator = "\n"

col_separator = "\t"


class CopySelectedCellsAction(qt.QAction):
    """QAction to copy text from selected cells in a :class:`QTableWidget`
    into the clipboard.

    If multiple cells are selected, the copied text will be a concatenation
    of the texts in all selected cells, tabulated with tabulation and
    newline characters.

    If the cells are sparsely selected, the structure is preserved by
    representing the unselected cells as empty strings in between two
    tabulation characters.
    Beware of pasting this data in another table widget, because depending
    on how the paste is implemented, the empty cells may cause data in the
    target table to be deleted, even though you didn't necessarily select the
    corresponding cell in the origin table.

    :param table: :class:`QTableView` to which this action belongs.
    """
    def __init__(self, table):
        if not isinstance(table, qt.QTableView):
            raise ValueError('CopySelectedCellsAction must be initialised ' +
                             'with a QTableWidget.')
        super(CopySelectedCellsAction, self).__init__(table)
        self.setText("Copy selection")
        self.setToolTip("Copy selected cells into the clipboard.")
        self.setShortcut(qt.QKeySequence.Copy)
        self.triggered.connect(self.copyCellsToClipboard)
        self.table = table
        self.cut = False
        """:attr:`cut` can be set to True by classes inheriting this action,
        to do a cut action."""

    def copyCellsToClipboard(self):
        """Concatenate the text content of all selected cells into a string
        using tabulations and newlines to keep the table structure.
        Put this text into the clipboard.
        """
        selected_idx = self.table.selectedIndexes()
        selected_idx_tuples = [(idx.row(), idx.column()) for idx in selected_idx]

        selected_rows = [idx[0] for idx in selected_idx_tuples]
        selected_columns = [idx[1] for idx in selected_idx_tuples]

        data_model = self.table.model()

        copied_text = ""
        for row in range(min(selected_rows), max(selected_rows) + 1):
            for col in range(min(selected_columns), max(selected_columns) + 1):
                index = data_model.index(row, col)
                cell_text = data_model.data(index)
                flags = data_model.flags(index)

                if (row, col) in selected_idx_tuples and cell_text is not None:
                    copied_text += cell_text
                    if self.cut and (flags & qt.Qt.ItemIsEditable):
                        data_model.setData(index, "")
                copied_text += col_separator
            # remove the right-most tabulation
            copied_text = copied_text[:-len(col_separator)]
            # add a newline
            copied_text += row_separator
        # remove final newline
        copied_text = copied_text[:-len(row_separator)]

        # put this text into clipboard
        qapp = qt.QApplication.instance()
        qapp.clipboard().setText(copied_text)


class CopyAllCellsAction(qt.QAction):
    """QAction to copy text from all cells in a :class:`QTableWidget`
    into the clipboard.

    The copied text will be a concatenation
    of the texts in all cells, tabulated with tabulation and
    newline characters.

    :param table: :class:`QTableView` to which this action belongs.
    """
    def __init__(self, table):
        if not isinstance(table, qt.QTableView):
            raise ValueError('CopyAllCellsAction must be initialised ' +
                             'with a QTableWidget.')
        super(CopyAllCellsAction, self).__init__(table)
        self.setText("Copy all")
        self.setToolTip("Copy all cells into the clipboard.")
        self.triggered.connect(self.copyCellsToClipboard)
        self.table = table
        self.cut = False

    def copyCellsToClipboard(self):
        """Concatenate the text content of all cells into a string
        using tabulations and newlines to keep the table structure.
        Put this text into the clipboard.
        """
        data_model = self.table.model()
        copied_text = ""
        for row in range(data_model.rowCount()):
            for col in range(data_model.columnCount()):
                index = data_model.index(row, col)
                cell_text = data_model.data(index)
                flags = data_model.flags(index)
                if cell_text is not None:
                    copied_text += cell_text
                    if self.cut and (flags & qt.Qt.ItemIsEditable):
                        data_model.setData(index, "")
                copied_text += col_separator
            # remove the right-most tabulation
            copied_text = copied_text[:-len(col_separator)]
            # add a newline
            copied_text += row_separator
        # remove final newline
        copied_text = copied_text[:-len(row_separator)]

        # put this text into clipboard
        qapp = qt.QApplication.instance()
        qapp.clipboard().setText(copied_text)


class CutSelectedCellsAction(CopySelectedCellsAction):
    """QAction to cut text from selected cells in a :class:`QTableWidget`
    into the clipboard.

    The text is deleted from the original table widget
    (use :class:`CopySelectedCellsAction` to preserve the original data).

    If multiple cells are selected, the cut text will be a concatenation
    of the texts in all selected cells, tabulated with tabulation and
    newline characters.

    If the cells are sparsely selected, the structure is preserved by
    representing the unselected cells as empty strings in between two
    tabulation characters.
    Beware of pasting this data in another table widget, because depending
    on how the paste is implemented, the empty cells may cause data in the
    target table to be deleted, even though you didn't necessarily select the
    corresponding cell in the origin table.

    :param table: :class:`QTableView` to which this action belongs."""
    def __init__(self, table):
        super(CutSelectedCellsAction, self).__init__(table)
        self.setText("Cut selection")
        self.setShortcut(qt.QKeySequence.Cut)
        # cutting is already implemented in CopySelectedCellsAction (but
        # it is disabled), we just need to enable it
        self.cut = True


class CutAllCellsAction(CopyAllCellsAction):
    """QAction to cut text from all cells in a :class:`QTableWidget`
    into the clipboard.

    The text is deleted from the original table widget
    (use :class:`CopyAllCellsAction` to preserve the original data).

    The cut text will be a concatenation
    of the texts in all cells, tabulated with tabulation and
    newline characters.

    :param table: :class:`QTableView` to which this action belongs."""
    def __init__(self, table):
        super(CutAllCellsAction, self).__init__(table)
        self.setText("Cut all")
        self.setToolTip("Cut all cells into the clipboard.")
        self.cut = True


def _parseTextAsTable(text, row_separator=row_separator, col_separator=col_separator):
    """Parse text into list of lists (2D sequence).

    The input text must be tabulated using tabulation characters and
    newlines to separate columns and rows.

    :param text: text to be parsed
    :param record_separator: String, or single character, to be interpreted
        as a record/row separator.
    :param field_separator: String, or single character, to be interpreted
        as a field/column separator.
    :return: 2D sequence of strings
    """
    rows = text.split(row_separator)
    table_data = [row.split(col_separator) for row in rows]
    return table_data


class PasteCellsAction(qt.QAction):
    """QAction to paste text from the clipboard into the table.

    If the text contains tabulations and
    newlines, they are interpreted as column and row separators.
    In such a case, the text is split into multiple texts to be pasted
    into multiple cells.

    If a cell content is an empty string in the original text, it is
    ignored: the destination cell's text will not be deleted.

    :param table: :class:`QTableView` to which this action belongs.
    """
    def __init__(self, table):
        if not isinstance(table, qt.QTableView):
            raise ValueError('PasteCellsAction must be initialised ' +
                             'with a QTableWidget.')
        super(PasteCellsAction, self).__init__(table)
        self.table = table
        self.setText("Paste")
        self.setShortcut(qt.QKeySequence.Paste)
        self.setToolTip("Paste data. The selected cell is the top-left" +
                        "corner of the paste area.")
        self.triggered.connect(self.pasteCellFromClipboard)

    def pasteCellFromClipboard(self):
        """Paste text from clipboard into the table.

        :return: *True* in case of success, *False* if pasting data failed.
        """
        selected_idx = self.table.selectedIndexes()
        if len(selected_idx) != 1:
            msgBox = qt.QMessageBox(parent=self.table)
            msgBox.setText("A single cell must be selected to paste data")
            msgBox.exec_()
            return False

        data_model = self.table.model()

        selected_row = selected_idx[0].row()
        selected_col = selected_idx[0].column()

        qapp = qt.QApplication.instance()
        clipboard_text = qapp.clipboard().text()
        table_data = _parseTextAsTable(clipboard_text)

        protected_cells = 0
        out_of_range_cells = 0

        # paste table data into cells, using selected cell as origin
        for row_offset in range(len(table_data)):
            for col_offset in range(len(table_data[row_offset])):
                target_row = selected_row + row_offset
                target_col = selected_col + col_offset

                if target_row >= data_model.rowCount() or\
                   target_col >= data_model.columnCount():
                    out_of_range_cells += 1
                    continue

                index = data_model.index(target_row, target_col)
                flags = data_model.flags(index)

                # ignore empty strings
                if table_data[row_offset][col_offset] != "":
                    if not flags & qt.Qt.ItemIsEditable:
                        protected_cells += 1
                        continue
                    data_model.setData(index, table_data[row_offset][col_offset])
                    # item.setText(table_data[row_offset][col_offset])

        if protected_cells or out_of_range_cells:
            msgBox = qt.QMessageBox(parent=self.table)
            msg = "Some data could not be inserted, "
            msg += "due to out-of-range or write-protected cells."
            msgBox.setText(msg)
            msgBox.exec_()
            return False
        return True


class TableWidget(qt.QTableWidget):
    """:class:`QTableWidget` with a context menu displaying up to 5 actions:

        - :class:`CopySelectedCellsAction`
        - :class:`CopyAllCellsAction`
        - :class:`CutSelectedCellsAction`
        - :class:`CutAllCellsAction`
        - :class:`PasteCellsAction`

    These actions interact with the clipboard and can be used to copy data
    to or from an external application, or another widget.

    The cut and paste actions are disabled by default, due to the risk of
    overwriting data (no *Undo* action is available). Use :meth:`enablePaste`
    and :meth:`enableCut` to activate them.

    :param parent: Parent QWidget
    :param bool cut: Enable cut action
    :param bool paste: Enable paste action
    """
    def __init__(self, parent=None, cut=False, paste=False):
        super(TableWidget, self).__init__(parent)
        self.addAction(CopySelectedCellsAction(self))
        self.addAction(CopyAllCellsAction(self))
        if cut:
            self.enableCut()
        if paste:
            self.enablePaste()

        self.setContextMenuPolicy(qt.Qt.ActionsContextMenu)

    def enablePaste(self):
        """Enable paste action, to paste data from the clipboard into the
        table.

        .. warning::

            This action can cause data to be overwritten.
            There is currently no *Undo* action to retrieve lost data.
        """
        self.addAction(PasteCellsAction(self))

    def enableCut(self):
        """Enable cut action.

        .. warning::

            This action can cause data to be deleted.
            There is currently no *Undo* action to retrieve lost data."""
        self.addAction(CutSelectedCellsAction(self))
        self.addAction(CutAllCellsAction(self))


class TableView(qt.QTableView):
    """:class:`QTableView` with a context menu displaying up to 5 actions:

        - :class:`CopySelectedCellsAction`
        - :class:`CopyAllCellsAction`
        - :class:`CutSelectedCellsAction`
        - :class:`CutAllCellsAction`
        - :class:`PasteCellsAction`

    These actions interact with the clipboard and can be used to copy data
    to or from an external application, or another widget.

    The cut and paste actions are disabled by default, due to the risk of
    overwriting data (no *Undo* action is available). Use :meth:`enablePaste`
    and :meth:`enableCut` to activate them.

    .. note::

        These actions will be available only after a model is associated
        with this view, using :meth:`setModel`.

    :param parent: Parent QWidget
    :param bool cut: Enable cut action
    :param bool paste: Enable paste action
    """
    def __init__(self, parent=None, cut=False, paste=False):
        super(TableView, self).__init__(parent)
        self.cut = cut
        self.paste = paste

    def setModel(self, model):
        """Set the data model for the table view, activate the actions
        and the context menu.

        :param model: :class:`qt.QAbstractItemModel` object
        """
        super(TableView, self).setModel(model)

        self.addAction(CopySelectedCellsAction(self))
        self.addAction(CopyAllCellsAction(self))
        if self.cut:
            self.enableCut()
        if self.paste:
            self.enablePaste()

        self.setContextMenuPolicy(qt.Qt.ActionsContextMenu)

    def enablePaste(self):
        """Enable paste action, to paste data from the clipboard into the
        table.

        .. warning::

            This action can cause data to be overwritten.
            There is currently no *Undo* action to retrieve lost data.
        """
        self.addAction(PasteCellsAction(self))

    def enableCut(self):
        """Enable cut action.

        .. warning::

            This action can cause data to be deleted.
            There is currently no *Undo* action to retrieve lost data.
        """
        self.addAction(CutSelectedCellsAction(self))
        self.addAction(CutAllCellsAction(self))

    def addAction(self, action):
        # ensure the actions are not added multiple times:
        # compare action type and parent widget with those of existing actions
        for existing_action in self.actions():
            if type(action) == type(existing_action):
                if hasattr(action, "table") and\
                        action.table is existing_action.table:
                    return None
        super(TableView, self).addAction(action)

if __name__ == "__main__":
    app = qt.QApplication([])

    tablewidget = TableWidget()
    tablewidget.setWindowTitle("TableWidget")
    tablewidget.setColumnCount(10)
    tablewidget.setRowCount(7)
    tablewidget.enableCut()
    tablewidget.enablePaste()
    tablewidget.show()

    tableview = TableView(cut=True, paste=True)
    tableview.setWindowTitle("TableView")
    model = qt.QStandardItemModel()
    model.setColumnCount(10)
    model.setRowCount(7)
    tableview.setModel(model)
    tableview.show()

    app.exec_()
