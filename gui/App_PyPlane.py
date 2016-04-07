# -*- coding: utf-8 -*-

#    Copyright (C) 2013
#    by Klemens Fritzsche, pyplane@leckstrom.de
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

__author__ = 'Klemens Fritzsche'
__version__ = "1.0"

# this file contains the central class that inherits from the base gui class (VIEW) that
# was created using qt4-designer and pyuic4
# the class pyplaneMainWindow represents the CONTROLLER element of the mvc-structure

from PyQt4 import QtGui
from PyQt4 import QtCore
import traceback
import sys
import os

import sympy as sp
from IPython import embed
import numpy as np
import ast

from Ui_PyPlane import Ui_pyplane
from core.Logging import myLogger
from core.ConfigHandler import myConfig
from core.System import System
import core.PyPlaneHelpers as myHelpers
from gui.Widgets import SettingsWidget

def handle_exception(error):

    myLogger.error_message("Error: An Python Exception occured.")
    myLogger.debug_message(str(type(error)))
    myLogger.debug_message(str(error))
    myLogger.message("See the log file config/logmessages.txt for full traceback ")

    exc_type, exc_value, exc_tb = sys.exc_info()
    lines = traceback.format_exception(exc_type, exc_value, exc_tb)
    tb_msg = "".join(lines)
    myLogger.append_to_file(tb_msg)

class PyplaneMainWindow(QtGui.QMainWindow, Ui_pyplane):
    def __init__(self, parent=None):
        super(PyplaneMainWindow, self).__init__()
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.setWindowTitle('PyPlane %s' % __version__)

        myLogger.register_output(self.logField)

        # Check if LaTeX and dvipng is installed on the system. This
        # is required in order to ensure that advanced formatting in
        # matplotlib works correctly (\left, \begin{array} etc.)
        self.latex_installed = myHelpers.check_if_latex()

        # Embed SettingsWidget:
        self.mySettings = SettingsWidget()
        self.SettingsLayout.addWidget(self.mySettings)

        self.fct_stack = []
        self.linearization_stack = []

        self.systems = []

        self.xDotLabel.setText(u"\u1E8B(x,y) = ")
        self.yDotLabel.setText(u"\u1E8F(x,y) = ")

        try:
            test = myConfig.read("Test", "test_var")
        except:
            test = "Could not load config file. Please check existence"

        myLogger.debug_message("Loading config file: " + test)

    def init(self):
        """ This function gets called only after program start.
        """
        # load tmp file
        try:
            self.load_tmp_system()
            self.disable_menu_items()
        except:
            pass

    def disable_menu_items(self):
        # uncheck items
        self.toggle_vectorfield_action.setChecked(False)
        self.toggle_streamlines_action.setChecked(False)
        self.toggle_equilibrium_action.setChecked(False)
        self.toggle_nullclines_action.setChecked(False)
        # shade out items:
        self.toggle_vectorfield_action.setEnabled(False)
        self.toggle_streamlines_action.setEnabled(False)
        self.toggle_equilibrium_action.setEnabled(False)
        self.toggle_nullclines_action.setEnabled(False)

    def update_ui(self):
        # unshade items
        self.toggle_vectorfield_action.setEnabled(True)
        self.toggle_streamlines_action.setEnabled(True)
        self.toggle_equilibrium_action.setEnabled(True)
        self.toggle_nullclines_action.setEnabled(True)

        # check items
        system = self.get_current_system()
        if hasattr(system, "Phaseplane"):
            if hasattr(system.Phaseplane, "VF"):
                self.toggle_vectorfield_action.setChecked(system.Phaseplane.VF.tgl)
            if hasattr(system.Phaseplane, "SL"):
                self.toggle_streamlines_action.setChecked(system.Phaseplane.SL.tgl)
            if hasattr(system.Phaseplane, "Equilibria"):
                self.toggle_equilibrium_action.setChecked(system.Phaseplane.Equilibria.tgl)
            if hasattr(system.Phaseplane, "Nullclines"):
                self.toggle_nullclines_action.setChecked(system.Phaseplane.Nullclines.tgl)
            # equation:
            self.xDotLineEdit.setText(system.equation.x_dot_string)
            self.yDotLineEdit.setText(system.equation.y_dot_string)

    def initialize_ui(self):
        # gets called after submitting a system (updae_ui() cannot be
        # used since the new system tab is not visible yet
        # values are taken from config file
        
        self.toggle_vectorfield_action.setChecked(myConfig.get_boolean("Vectorfield", "vf_onByDefault"))
        self.toggle_streamlines_action.setChecked(myConfig.get_boolean("Streamlines", "stream_onByDefault"))
        self.toggle_equilibrium_action.setChecked(False)
        self.toggle_nullclines_action.setChecked(myConfig.get_boolean("Nullclines", "nc_onByDefault"))
        

    def new_linearized_system(self, nonlinear_system, jacobian, equilibrium):
        pass
    def new_linearized_system1(self, nonlinear_system, jacobian, equilibrium):
        # TODO: REFACTOR THIS FUNCTION!!!
        self.nonlinear_system = nonlinear_system
        eq0 = str(jacobian[0,0])+"*x + "+str(jacobian[0,1])+"*y"
        eq1 = str(jacobian[1,0])+"*x + "+str(jacobian[1,1])+"*y"
        equation = (eq0, eq1)
        system = System(self, equation, linear=True)
        self.systems.insert(0, system)

        # TODO: window range should be equal to window range of phase plane

        # TODO: make set_window_range-funtion reusable for this case
        #~ xmin = float(self.PP_xminLineEdit.text())
        #~ xmax = float(self.PP_xmaxLineEdit.text())
        #~ ymin = float(self.PP_yminLineEdit.text())
        #~ ymax = float(self.PP_ymaxLineEdit.text())


        xe = equilibrium[0]
        ye = equilibrium[1]
        x_dot_string = str(jacobian[0,0]) + "*(x-(" + str(xe) + ")) + (" + str(jacobian[0,1]) + ")*(y-(" + str(ye) + "))"
        y_dot_string = str(jacobian[1,0]) + "*(x-(" + str(xe) + ")) + (" + str(jacobian[1,1]) + ")*(y-(" + str(ye) + "))"

        #title_matrix = r"$A=\begin{Bmatrix}"+str(jac[0,0])+r" & "+str(jac[0,1])+r" \\"+str(jac[1,0])+r" & "+str(jac[1,1])+r"\end{Bmatrix}$"

        # set title
        lin_round = int(myConfig.read("Linearization", "lin_round_decimals")) # display rounded floats
        A00 = str(round(jacobian[0,0],lin_round))
        A01 = str(round(jacobian[0,1],lin_round))
        A11 = str(round(jacobian[1,1],lin_round))
        A10 = str(round(jacobian[1,0],lin_round))
        if self.latex_installed == True:
            title_matrix = r'$\underline{A}_{' + str(len(self.linearization_stack)) + r'} = \left( \begin{array}{ll} ' + A00 + r' & ' + A01 + r'\\ ' + A10 + r' & ' + A11 + r' \end{array} \right)$'
        else:
            title_matrix = r'$a_{11}(' + str(len(self.linearization_stack)) + r') =  ' + A00 + r', a_{12}(' + str(len(self.linearization_stack)) + r') = ' + A01 + '$\n $a_{21}( ' + str(len(self.linearization_stack)) + r') = ' + A10 +  r', a_{22}(' + str(len(self.linearization_stack)) + r') = ' + A11 + r'$'


        # calculating eigenvalues and eigenvectors:
        eigenvalues, eigenvectors = system.Phaseplane.Equilibria.get_eigenval_eigenvec(equilibrium)
        myLogger.message("Eigenvectors: (" + str(eigenvectors[0][0]) + ", " + str(eigenvectors[0][1]) + ") and (" + str(eigenvectors[1][0]) + ", " + str(eigenvectors[1][1]) + ")")

        # scaling
        d1 = (xmax-xmin)/10
        d2 = (ymax-ymin)/10
        d_large = (xmax-xmin)*(ymax-ymin)
        
        EV0 = np.array([np.real(eigenvectors[0][0]),np.real(eigenvectors[0][1])])
        EV0_norm = np.sqrt(EV0[0]**2+EV0[1]**2)
        EV0_scaled = np.array([d1*(1/EV0_norm)*EV0[0],d1*(1/EV0_norm)*EV0[1]])

        EV1 = np.array([np.real(eigenvectors[1][0]),np.real(eigenvectors[1][1])])
        EV1_norm = np.sqrt(EV1[0]**2+EV1[1]**2)
        EV1_scaled = np.array([d1*(1/EV1_norm)*EV1[0],d1*(1/EV1_norm)*EV1[1]])
        
        # plot eigenvectors:
        color_eigenvec = myConfig.read("Linearization", "lin_eigenvector_color")
        color_eigenline = myConfig.read("Linearization", "lin_eigenvector_linecolor")

        if myConfig.get_boolean("Linearization","lin_show_eigenline"):
            system.Phaseplane.Plot.canvas.axes.arrow(equilibrium[0], equilibrium[1], d_large*EV0_scaled[0], d_large*EV0_scaled[1], head_width=0, head_length=0, color=color_eigenline)
            system.Phaseplane.Plot.canvas.axes.arrow(equilibrium[0], equilibrium[1], -d_large*EV0_scaled[0], -d_large*EV0_scaled[1], head_width=0, head_length=0, color=color_eigenline)
        if myConfig.get_boolean("Linearization","lin_show_eigenvector"):
            system.Phaseplane.Plot.canvas.axes.arrow(equilibrium[0], equilibrium[1], EV0_scaled[0], EV0_scaled[1], head_width=0, head_length=0, color=color_eigenvec)
        
        if myConfig.get_boolean("Linearization","lin_show_eigenline"):
            system.Phaseplane.Plot.canvas.axes.arrow(equilibrium[0], equilibrium[1], d_large*EV1_scaled[0], d_large*EV1_scaled[1], head_width=0, head_length=0, color=color_eigenline)
            system.Phaseplane.Plot.canvasn.axes.arrow(equilibrium[0], equilibrium[1], -d_large*EV1_scaled[0], -d_large*EV1_scaled[1], head_width=0, head_length=0, color=color_eigenline)
        if myConfig.get_boolean("Linearization","lin_show_eigenvector"):
            system.Phaseplane.Plot.canvas.axes.arrow(equilibrium[0], equilibrium[1], EV1_scaled[0], EV1_scaled[1], head_width=0, head_length=0, color=color_eigenvec)

        # characterize EP:
        # stable focus:     SFOC
        # unstable focus:   UFOC
        # focus:            FOC
        # stable node:      SNOD
        # unstable node:    UNOD
        # saddle:           SAD

        determinant = jacobian[0,0]*jacobian[1,1] - jacobian[1,0]*jacobian[0,1]
        trace = jacobian[0,0] + jacobian[1,1]

        ep_character = ""

        if trace==0 and determinant==0:
            ep_character = "Unclassified"

        elif determinant < 0:
            ep_character = "Saddle"

        elif (determinant > 0) and (determinant < ((trace**2)/4)):
            if trace < 0:
                ep_character = "Nodal Sink"
            elif trace > 0:
                ep_character = "Nodal Source"

        elif determinant > ((trace**2)/4):
            if trace == 0:
                ep_character = "Center"
            elif trace < 0:
                ep_character = "Spiral Sink"
            elif trace > 0:
                ep_character = "Spiral Source"
        elif determinant == ((trace**2)/4):
            if trace < 0:
                ep_character = "Sink"
            elif trace > 0:
                ep_character = "Source"

        if myConfig.get_boolean(section, token + "showTitle"):
            eq_x_rounded = str(round(equilibrium[0],lin_round))
            eq_y_rounded = str(round(equilibrium[1],lin_round))
            title1 = ep_character + r' at $(' + eq_x_rounded + r', ' + eq_y_rounded + r')$'
            #~ title1 = r'Equilibrium point ' + str(len(self.linearization_stack)) + r', ' + ep_character + r' at $(' + eq_x_rounded + r', ' + eq_y_rounded + r')$'
            #self.plotCanvas_Lin.axes.set_title(str(title1)+"$\n$\\dot{x} = " + x_dot_string + "$\n$\\dot{y} = " + y_dot_string + "$", loc='center')
            system.Phaseplane.Plot.canvas.axes.set_title(str(title1)+"\n"+title_matrix, fontsize=11)
        else:
            system.Phaseplane.Plot.canvas.fig.subplots_adjust(top=0.99)

        # mark EP in linearized tab
        system.Phaseplane.Plot.canvas.axes.plot(equilibrium[0], equilibrium[1],'ro')

        # add annotation in phaseplane
        label = str(ep_character)

        system.Phaseplane.Plot.canvas.text(equilibrium[0], equilibrium[1], label, fontsize=10)

        system.Phaseplane.Plot.canvas.draw()

        # plot vectorfield
        linearized_vectorfield.update()

        #~ title = str(ep_character)
        #~ self.index = self.tabWidget.addTab(contents, title)

        #~ self.linearization_stack.append(equilibrium)

        #QtCore.pyqtRemoveInputHook()
        #embed()

    def close_current_tab(self):
        index = self.tabWidget.currentIndex()
        if index != self.tabWidget.count()-1:
            self.tabWidget.removeTab(index)
            self.systems.pop(index)

    def close_all_tabs(self):
        # TODO: something is wrong here: settings tab gets removed
        #       sometimes!
        for i in xrange(self.tabWidget.count()-1):
            self.tabWidget.removeTab(i)
            # TODO: Delete Data

    def initialize_new_system_tab(self):
        # Create new system tab
        self.mySystemTab = SystemTabWidget()
        contents = QtGui.QWidget(self.tabWidget)
        self.mySystemTab.setupUi(contents)

        number = self.tabWidget.count()
        self.tabWidget.insertTab(0, contents, "System %s" % (str(number)))
        self.tabWidget.setCurrentIndex(0)

        # TODO: check why this can't be done within the SystemTabWidget
        #       class!
        self.ppWidget = PhaseplaneWidget(self)
        self.mySystemTab.ppLayout.addWidget(self.ppWidget)
        self.xWidget = ZoomWidgetSimple()
        self.mySystemTab.xLayout.addWidget(self.xWidget)
        self.yWidget = ZoomWidgetSimple()
        self.mySystemTab.yLayout.addWidget(self.yWidget)

    def new_system(self, equation):
        system = System(self, equation)
        self.systems.insert(0, system)

    def submit(self):
        """ This function gets called after clicking on the submit button
        """
        try:
            xtxt = str(self.xDotLineEdit.text())
            ytxt = str(self.yDotLineEdit.text())
        except UnicodeEncodeError as exc:
            myLogger.warn_message("UnicodeEncodeError! Please check input.")
            myLogger.debug_message(str(exc))
        else:
            cond1 = str(self.xDotLineEdit.text()) != ""
            cond2 = str(self.yDotLineEdit.text()) != ""

            if cond1 and cond2:
                x_string = str(self.xDotLineEdit.text())
                y_string = str(self.yDotLineEdit.text())

                equation = (x_string, y_string)
                system = System(self, equation)
                self.systems.insert(0, system)

                myLogger.message("------ new system created ------")
                myLogger.message("    x' = " + str(system.equation.what_is_my_system()[0]))
                myLogger.message("    y' = " + str(system.equation.what_is_my_system()[1]) + "\n", )

            else:
                myLogger.error_message("Please check system!")


    def load_system(self, file_name):
        """ load previous system (from tmp file) """

        with open(file_name, 'r') as sysfile:
    # TODO: This does not work, but how would i find a way to store a
    #       system?
            #~ pps_file = pcl.loads(sysfile.read())
            #~ system = System(self)
            #~ system.unpickle(pps_file)
            #~ self.systems.insert(0, system)
            #~ self.xDotLineEdit.setText(sysfile.readline().strip())
            #~ self.yDotLineEdit.setText(sysfile.readline().strip())
            xdot_string = str(sysfile.readline())
            ydot_string = str(sysfile.readline())
            self.xDotLineEdit.setText(xdot_string.strip())
            self.yDotLineEdit.setText(ydot_string.strip())
            myLogger.message(file_name + " loaded")

    def load_tmp_system(self):
        self.load_system('library/tmp.ppf')

    def load_system_from_file(self):
        file_name = QtGui.QFileDialog.getOpenFileName(self,
                                                      'Open pyplane file', '',
                                                      'pyplane file (*.ppf)')
        if len(file_name) > 0:
            self.load_system(file_name)

        self.submit()
        self.update_ui()

    def save_file(self):
        if len(self.systems) > 0:
            index = self.tabWidget.currentIndex()
            system = self.systems[index]
            file_name, filter = QtGui.QFileDialog.getSaveFileNameAndFilter(self,
                                                                           'Save pyplane file', '',
                                                                           'pyplane file (*.ppf)')
            #~ sys_pickleds = system.pickle(file_name)
            #~ system.equation.what_is_my_system()
            self.save_system(file_name, system.equation.what_is_my_system())
        else:
            myLogger.error_message("There is no system to save!")


    def save_system(self, file_name, system):
        x_dot_string = str(system[0])
        y_dot_string = str(system[1])
        f_ending = '.ppf'
        f_len = len(file_name)

        if file_name[f_len - 4:f_len] == f_ending:
            with open(file_name, 'w') as sysfile:
                sysfile.write(x_dot_string + "\n" + y_dot_string)
        else:
            with open(file_name + f_ending, 'w') as sysfile:
                sysfile.write(x_dot_string + "\n" + y_dot_string)

        myLogger.message("System saved as " + file_name)

    def export_as(self):
        """ export dialog for pyplane plot
        """

        q_files_types = QtCore.QString(".png;;.svg;;.pdf;;.eps")
        q_file_name, q_file_type = QtGui.QFileDialog.getSaveFileNameAndFilter(self,
                                                                       "Export PyPlane Plot as .png, .svg, .pdf, or .eps-file", "",
                                                                       q_files_types)
        # Ensure we are out of the QString world in the following                                                               
        file_name = str(q_file_name)
        file_type = str(q_file_type)
            
        if file_name:
            # Fix: Under some KDE's the file_type is returned empty because
            # of a "DBUS-error". Hence, in such cases, we try to take the 
            # file_type from the extension specified by the user . If no valid extension 
            # is set by the user file_type is set to png. This bugfix is addressed
            # in the first part of the "if not" structure.
            #
            # In the else part of the "if not" structure the case is handled
            # where the user wants to have dots in the basename of the file
            # (affects all operating systems)
            #
            file_name2, file_type2 = os.path.splitext(file_name)
            if not file_type:
                if file_type2 not in [".png", ".svg", ".pdf", ".eps"]:                    
                    file_type = ".png"
                else:
                    # Allow things like figure.case21.pdf
                    file_name = file_name2
                    file_type = file_type2
            else:
                # This part runs on non KDE-systems or KDE-systems without
                # the DBUS error:                
                # drop accidently added duplicate file extensions
                # (avoid figure.png.png but allow figure.case1.png)
                if file_type2 == file_type:
                    file_name = file_name2
            # ------

            if file_type == ".png":
                self.export_as_png(file_name)
            elif file_type == ".svg":
                self.export_as_svg(file_name)
            elif file_type == ".pdf":
                self.export_as_pdf(file_name)
            elif file_type == ".eps":
                self.export_as_eps(file_name)
            else:
                myLogger.error_message("Filetype-Error")

    def update_window_range_lineedits(self):
        """ this function will update_all every window size line edit
        """

        # phase plane
        xmin1, xmax1, ymin1, ymax1 = self.myGraph.get_limits(self.myGraph.plot_pp)
        self.PP_xminLineEdit.setText(str(round(xmin1, 2)))
        self.PP_xmaxLineEdit.setText(str(round(xmax1, 2)))
        self.PP_yminLineEdit.setText(str(round(ymin1, 2)))
        self.PP_ymaxLineEdit.setText(str(round(ymax1, 2)))

        # x(t)
        xmin2, xmax2, ymin2, ymax2 = self.myGraph.get_limits(self.myGraph.plot_x)
        self.X_tminLineEdit.setText(str(round(xmin2, 2)))
        self.X_tmaxLineEdit.setText(str(round(xmax2, 2)))
        self.X_xminLineEdit.setText(str(round(ymin2, 2)))
        self.X_xmaxLineEdit.setText(str(round(ymax2, 2)))

        # y(t)
        xmin3, xmax3, ymin3, ymax3 = self.myGraph.get_limits(self.myGraph.plot_y)
        self.Y_tminLineEdit.setText(str(round(xmin3, 2)))
        self.Y_tmaxLineEdit.setText(str(round(xmax3, 2)))
        self.Y_yminLineEdit.setText(str(round(ymin3, 2)))
        self.Y_ymaxLineEdit.setText(str(round(ymax3, 2)))

    def export_as_png(self, filename):

        filename_pp = str(filename) + "_pp.png"
        self.myGraph.plot_pp.fig.savefig(filename_pp,
                                         bbox_inches='tight')

        filename_x = str(filename) + "_x.png"
        self.myGraph.plot_x.fig.savefig(filename_x, bbox_inches='tight')

        filename_y = str(filename) + "_y.png"
        self.myGraph.plot_y.fig.savefig(filename_y, bbox_inches='tight')

        myLogger.message(
            "plot exported as\n\t" + filename_pp + ",\n\t" + filename_x + ",\n\t" + filename_y)

    def export_as_svg(self, filename):
        filename_pp = str(filename) + "_pp.svg"
        self.myGraph.plot_pp.fig.savefig(filename_pp, bbox_inches='tight')

        filename_x = str(filename) + "_x.svg"
        self.myGraph.plot_x.fig.savefig(filename_x, bbox_inches='tight')

        filename_y = str(filename) + "_y.svg"
        self.myGraph.plot_y.fig.savefig(filename_y, bbox_inches='tight')

        myLogger.message("plot exported as\n\t" + filename_pp + ",\n\t" + filename_x + ",\n\t" + filename_y)

    def export_as_eps(self, filename):
        filename_pp = str(filename) + "_pp.eps"

        self.myGraph.plot_pp.fig.savefig(filename_pp, bbox_inches='tight')

        filename_x = str(filename) + "_x.eps"
        self.myGraph.plot_x.fig.savefig(filename_x, bbox_inches='tight')

        filename_y = str(filename) + "_y.eps"
        self.myGraph.plot_y.fig.savefig(filename_y, bbox_inches='tight')

        myLogger.message("plot exported as\n\t" + filename_pp + ",\n\t" + filename_x + ",\n\t" + filename_y)

    def export_as_pdf(self, filename):
        filename_pp = str(filename) + "_pp.pdf"
        self.myGraph.plot_pp.fig.savefig(filename_pp, bbox_inches='tight')

        filename_x = str(filename) + "_x.pdf"
        self.myGraph.plot_x.fig.savefig(filename_x, bbox_inches='tight')

        filename_y = str(filename) + "_y.pdf"
        self.myGraph.plot_y.fig.savefig(filename_y, bbox_inches='tight')

        myLogger.message("plot exported as\n\t" + filename_pp + ",\n\t" + filename_x + ",\n\t" + filename_y)

    def add_function_to_plot(self):
        """ will plot additional functions and put it on a stack
        """
        self.x = sp.symbols('x')
        self.y = sp.symbols('y')
        self.fct = None

        try:
            fct_txt = str(self.yLineEdit.text())
        except UnicodeEncodeError as exc:
            myLogger.error_message("input error!")
            myLogger.debug_message(str(exc))

        if fct_txt != "":
            try:
                self.fct_string = str(self.yLineEdit.text())

                self.fct_expr = sp.sympify(self.fct_string)
                # self.fct = sp.lambdify(self.x,self.fct_expr,'numpy')
                self.fct = sp.lambdify((self.x, self.y), self.fct_expr, 'numpy')
                xmin, xmax, ymin, ymax = self.myGraph.get_limits(self.myGraph.plot_pp)

                # plot the function for an x-interval twice as big as the current window
                deltax = (xmax - xmin) / 2
                deltay = (ymax - ymin) / 2
                plot_xmin = xmin - deltax
                plot_xmax = xmax + deltax
                plot_ymin = ymin - deltay
                plot_ymax = ymax + deltay

                pts_in_x = int(myConfig.read("Functions", "fct_gridPointsInX"))
                pts_in_y = int(myConfig.read("Functions", "fct_gridPointsInY"))

                fct_color = myConfig.read("Functions", "fct_color")
                fct_linewidth = float(myConfig.read("Functions", "fct_linewidth"))

                x = np.arange(plot_xmin, plot_xmax, (xmax - xmin) / pts_in_x)
                y = np.arange(plot_ymin, plot_ymax, (ymax - ymin) / pts_in_y)

                X, Y = np.meshgrid(x, y)

                #yvalue = self.fct(xvalue)

                myfunc = self.fct(X, Y)
                # TODO: plots like y=1/x have a connection between -inf and +inf that is not actually there!

                # plot function and put on function-stack
                new_fct = self.myGraph.plot_pp.axes.contour(X, Y, myfunc, [0],
                                                            zorder=100,
                                                            linewidths=fct_linewidth,
                                                            colors=fct_color)
                # new_fct = self.myGraph.plot_pp.axes.plot(xvalue, yvalue, label="fct", color="green")
                self.fct_stack.append(new_fct)

                self.myGraph.update_graph(self.myGraph.plot_pp)
                myLogger.message("function plot: 0 = " + self.fct_string)

            except Exception as error:
                handle_exception(error)
        else:
            myLogger.error_message("Please enter function.")

    def remove_function_from_plot(self):
        if len(self.fct_stack) != 0:
            for i in xrange(0, len(self.fct_stack)):
                fct = self.fct_stack.pop().collections
                for j in xrange(0, len(fct)):
                    try:
                        fct[j].remove()
                    except Exception as error:
                        myLogger.debug_message("couldn't delete function")
                        myLogger.debug_message(str(type(error)))
                        myLogger.debug_message(str(error))
            myLogger.message("functions removed")
        else:
            myLogger.debug_message("no function to delete")

        self.myGraph.update_graph(self.myGraph.plot_pp)

#     def addFctClear(self):
#         """ will remove every additional function
#         """
#         if len(self.fct_stack)!=0:
#             for i in xrange(0,len(self.fct_stack)):
#                 try:
#                     self.fct_stack.pop()[0].remove()
#                 except Exception as error:
#                     myLogger.debug_message("couldn't delete function plot")
#                     myLogger.debug_message(str(type(error)))
#                     myLogger.debug_message(str(error))
#
#             myLogger.message("function plots removed")
#             self.myGraph.update_graph(self.myGraph.plot_pp)
#         else:
#             myLogger.warn_message("no additional function has been plotted")

if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    window_object = PyplaneMainWindow()
    window_object.showFullScreen()
    window_object.show()
    app.exec_()
