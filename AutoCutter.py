import tkinter as tk
from tkinter.filedialog import asksaveasfile
from tkinter.filedialog import askopenfile
from math               import sqrt
from copy               import deepcopy
from time               import localtime
from PIL                import Image as PIMG

import os, threading, shutil, sys, platform, subprocess
import numpy as np

"""Written By Rokas Gerulskis in the research group of Shelley D. Minteer at the University of Utah in 2022 and Licensed under GNU General Public License v3.0"""

roots = []
default = '''area = 0.25
FAWidth = False
FAHeight = False
rowCount = 4
trodesPerRow = False
trodeLen = False
pixPerCm = 500
minMargin = .75
LRMargin = False
TBMargin = False
sheetWidth = 10
sheetHeight = 10
yGapH = 0.036
endYGapH = 0.044
xGapW = 0.036
faMarkW = 0.126
rowThread = 1'''

valuesSet = '''[self.Warea.get(), self.WFAWidth.get(), self.WFAHeight.get(), self.WrowCount.get(), self.WtrodesPerRow.get(), self.WtrodeLen.get(),
                  self.WpixPerCm.get(),
                  self.WminMargin.get(), self.WLRMargin.get(), self.WTBMargin.get(), self.WsheetWidth.get(),
                  self.WsheetHeight.get(),
                  self.WyGapH.get(), self.WendYGapH.get(), self.WxGapW.get(), self.faMarkW.get(), self.rowThread]'''
tooltips = {"area":         '(cm\u00b2) area of functional area.\nset False to calculate automatically from FAWidth and FAHeight.\nIf all three are provided, area is ignored and functional area is calculated from FAWidth and FAHeight.',
            "FAWidth":      '(cm) horizontal length of functional area. \nset False to calculate automatically from area alone or area and FAHeight.',
            "FAHeight":     '(cm) vertical length of functional area.\nset False to calculate automatically from area alone or area and FAWidth.',
            "rowCount":     '(integer) number of rows to cut.\nset False to calculate automatically from trodeLen.',
            "trodesPerRow": '(integer) number of electrodes per row.\nset False to calculate from area and minMargin/LRMargin.',
            "trodeLen":     '(cm) total length of electrodes.\nset False to calculate automatically from rowCount and minMargin/TBMargin.',
            "pixPerCm":     '(pixels/cm) resolution of image.\ndefault 500 pixels/cm gives very high accuracy.\n higher values can lead to failure from memory errors.',
            "minMargin":    '(cm) width of framing paper which will not be cut.\nOnly need enough to tape 1-2 mm of CP on either side to backing paper.\nUsed to calculate LRMargin and TBMargin below if they are not provided.',
            "LRMargin":     '(cm) as minMargin, but only left and right side.\nFalse to calculate from minMargin.',
            "TBMargin":     '(cm) as minMargin, but only top and bottom.\nLess important, even 0.094 cm should suffice if necessary.\nFalse to calculate from minMargin.',
            "sheetWidth":   '(cm) total width of carbon paper.',
            "sheetHeight":  '(cm) total height of carbon paper.',
            "yGapH":        '(cm) height of y axis gaps (linkers between electrodes).\n0.036 cm is sufficient for 2 cm electrodes.\nthicker may be necessary for longer electrodes.',
            "endYGapH":     '(cm) as yGapH but between left/right-most electrodes and supporting frame.\n0.044 cm is sufficient for 2 cm electrodes.',
            "xGapW":        '(cm) width of x axis gaps (linkers on bottom of electrodes).\n0.044 cm is sufficient for 2 cm electrodes, likely sufficient universally.',
            "faMarkW":      '(cm) width of functional area marker which defines maximum waxing distance.\n0.126 cm should be universal.',
            "rowThread":    'Generate rows in separate threads. Significantly faster.\ndisable if program fails without giving an error (memory error).'}
                                                #tooltips that appear when hovering over an input
varNames = [key for key in tooltips.keys()]
mainWins = []                                   #list of main windows, more are added with self.new()

############################################fix opening errored window. should open default instead.

def intr(aFloat):
    """rounds a float to an int since int() only rounds down and round() only returns floats"""
    return int(round(aFloat,0))

def open_folder(path):
    """opens a folder for user to view contents. Used to open output folder with images./n originally written by Cas on Stackoverflow."""
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

ACdir        = os.path.dirname(os.path.abspath(__file__))
ACdir        = resource_path(ACdir)
guideImgPath = ACdir + r'\guide.png'

class mainWin:
    """main window in which parameters are input"""
    def __init__(self, inParams=default, fiPath = None, new = False):
        global mainWins
        # initial vars
        self.retry      = False
        self.inParams   = inParams                              #unprocessed param txt
        self.params     = {}                                    
        self.icon       = ACdir+ r'/icon.ico'            #icon in corner of GUI window
        # updated vars
        self.responses  = ''                                    #responses stored here to output in outWin after process is run
        self.fiPath     = fiPath                                #when params are loaded as a file
        self.dirPath    = None
        self.fiName     = "New Cut"
        self.rowThread  = 1
        if self.fiPath:
            self.fiName        = self.fiPath.split('/')[-1].replace('.txt','')
            self.dirPath       = '/'.join(self.fiPath.split('/')[:-1])
            print(self.dirPath)

        self.outWins    = []                                    #child output windows run by instance of program
        self.helpWins   = []                                    #child input guide windows
        self.erWins     = []                                    #child file load error windows
        # start window
        fresh = True
        self.root       = tk.Tk()
        self.location   = len(mainWins)
        mainWins        .append(self.root)

        if fresh:
            self.root.focus_force()
            fresh = False
        self.root       .title(self.fiName)                          #title of window
        roots           .append(self.root)                      #global set of windows, may be deprecated
        self.root       .iconbitmap(self.icon)                  #window icon is set
        self.root       .minsize(232,530)
        self.root       .maxsize(232, 530)
        self.mb         = tk.Menu(self.root)                                        #file/help parent menu
        self.mb_fm      = tk.Menu(self.mb, tearoff=0)
        self.mb_fm      .add_command(label="New", command=self.restart)
        self.root       .bind("<Control-n>", self.restart)
        self.mb_fm      .add_command(label="Open", command=self.openFile)
        self.root       .bind("<Control-o>", self.openFile)
        self.mb_fm      .add_command(label="Save", command=self.save)
        self.root       .bind("<Control-s>", self.save)
        self.root       .bind("<Control-w>", self.close)

        self.mb_fm      .add_command(label="Save as...", command=self.saveAs)
        self.mb         .add_cascade(label="File", menu=self.mb_fm)                 #'file' cascade
        self.mb_hm      = tk.Menu(self.mb, tearoff=0)
        self.mb_hm      .add_command(label="Input Guide", command=self.makeAHelp)
        self.mb_hm      .add_command(label="About...", command=self.info)
        self.mb         .add_cascade(label="Help", menu=self.mb_hm)                 #'help' cascade
        self.root       .config(menu=self.mb)

        responses = self.cleanParams()
        if responses:
            print(responses)
            self.makeAnErr(responses)
            self.restart()

        self.Whoover        = self.aLabel(self, "hover over an entry for info\ncheck Help > Input Guide\n for explanations", 0, font = "helvetica 10 bold",)
        self.WprimVars      = self.aLabel(self, " ", 1)

        self.Warea          = self.anEntry(self, "area", 2)
        self.WFAWidth        = self.anEntry(self, 'FAWidth', 3)
        self.WFAHeight      = self.anEntry(self, 'FAHeight', 4)
        self.WrowCount      = self.anEntry(self, "rowCount", 5)
        self.WtrodesPerRow  = self.anEntry(self, "trodesPerRow", 6)
        self.WtrodeLen      = self.anEntry(self, "trodeLen", 7)

        self.WadvVars       = self.aLabel(self, "advanced variables (defaults likely OK)", 8)

        self.WpixPerCm      = self.anEntry(self, "pixPerCm", 9)
        self.WminMargin     = self.anEntry(self, "minMargin", 10)
        self.WLRMargin      = self.anEntry(self, "LRMargin", 11)
        self.WTBMargin      = self.anEntry(self, "TBMargin", 12)
        self.WsheetWidth    = self.anEntry(self, "sheetWidth", 13)
        self.WsheetHeight   = self.anEntry(self, "sheetHeight", 14)
        self.WyGapH         = self.anEntry(self, "yGapH", 15)
        self.WendYGapH      = self.anEntry(self, "endYGapH", 16)
        self.WxGapW         = self.anEntry(self, "xGapW", 17)
        self.faMarkW        = self.anEntry(self, "faMarkW",18)

        self.chkThread      = tk.Checkbutton(self.root, text= 'thread rows', variable = self.rowThread)
        self.chkThread      .grid(row = 19, columnspan=3)
        self.chkThread      .select()
        self                .CreateToolTip(self.chkThread, text=tooltips['rowThread'])

        self.button         = tk.Button(self.root, text='start', width=5, command=self.makeAnOut)
        self.button         .grid(row=21, column=0, columnspan=3, pady=(10, 5))
        self.root           .mainloop()

    def cleanParams(self):
        """attempts to extract params from loaded txt of parameters.
        Default is stored as a string but gets processed the same way"""
        inParams = self.inParams
        inParams = inParams.split('\n')
        inParams = [i for i in inParams if i != '']
        lostKeys = []

        for item in inParams:
            sItem = item.split('=')
            if len(sItem) == 2:
                key, value = sItem[0].strip(), sItem[1].strip()
                self.params[key] = value

        for key in varNames:
            if key not in self.params.keys():
                lostKeys.append(key)

        if lostKeys:
            responses = "\nloaded file is missing the following keys:\n\n" + '\n'.join(lostKeys) +'\n\n loading default keys instead.'
            return responses

    class anEr:
        """error window that displays when input file has errors"""
        def __init__(self, parent, message):
            self.parent       = parent
            self.root         = tk.Toplevel(parent.root)
            self.root         .title("load error!")
            self.root         .iconbitmap(parent.icon)
            self.out          = parent.aLabel(self, message, 0)
            self.gap          = parent.aLabel(self, " ", 1)
            self.ok           = tk.Button(self.root, text='okay', width=5, command=self.delete)
            self.ok           .grid(row = 2, columnspan = 3, sticky = 's', pady = (0,5))
            self.ok           .focus_force()
            self.root         .mainloop()

        def delete(self):
            self.root.destroy()
            self.parent.restart()

    class anEntry:
        """defines a row in mainWin: a label, input box, associates tooltip with input box"""
        def __init__(self, parent, label, rowNum):
            self.label      = label
            self.rowNum     = rowNum
            self.parent     = parent
            self.defaultVar = str(self.parent.params[self.label])
            self.tooltip    = tooltips[label]
            self.Wlabel     = tk.Label(parent.root, text=self.label)
            self.Wlabel     .grid(row=self.rowNum, column=0)
            self.WEntry     = tk.Entry(parent.root)
            self.WEntry     .grid(row=rowNum, column=1)
            self.WEntry     .insert(0, self.defaultVar)
            parent          .CreateToolTip(self.WEntry, text=self.tooltip)

        def get(self):
            return self.WEntry.get()

    class aLabel:
        """as anEntry, but defines a row when it contains only a label"""
        def __init__(self, parent, label, rowNum, font = None):
            self.label      = label
            self.rowNum     = rowNum

            self.Wlabel     = tk.Label(parent.root, text=self.label, font = font)
            self.Wlabel     .grid(row=rowNum, column=0, columnspan=2, pady=(10, 0), padx=(10, 10))

    class ToolTip(object):
        """tooltips that display when hovering over an input window. Originally written by squareRoot17 on stackoverflow."""
        def __init__(self, widget):
            self.widget     = widget
            self.tipwindow  = None
            self.id         = None
            self.x = self.y = 0

        def showtip(self, text):
            "Display text in tooltip window"
            self.text = text
            if self.tipwindow or not self.text:
                return
            x, y, cx, cy = self.widget.bbox("insert")
            x = x + self.widget.winfo_rootx() + 57
            y = y + cy + self.widget.winfo_rooty() + 27
            self.tipwindow = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(1)
            tw.wm_geometry("+%d+%d" % (x, y))
            label = tk.Label(tw, text=self.text, justify="left",
                             background="#ffffe0", relief="solid", borderwidth=1,
                             font=("tahoma", "8", "normal"))
            label.pack(ipadx=1)

        def hidetip(self):
            tw = self.tipwindow
            self.tipwindow = None
            if tw:
                tw.destroy()

    def CreateToolTip(self, widget, text):
        """creates an instance of ToolTip class when hovering over an input.
        Originally written by squareRoot17 on stackoverflow."""

        toolTip = self.ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def info(self):
        """placeholder function. will be deleted when program is published and info menu can contain publication info"""
        infoWin         = tk.Toplevel(self.root)
        infoWin         .iconbitmap(self.icon)
        infoWin         .focus()
        infoWin         .title("About AutoCutter")
        infoText        = "\nAutoCutter written by Rokas Gerulskis in 2022\n\n for use in papers please cite:\n\n#####\n"
        text            = tk.Label(infoWin, text=infoText)
        text            .pack()

    def close(self, event=False):
        self.root.destroy()

    def restart(self, event=False, params=default):
        self.root.destroy()
        del mainWins[self.location]
        mainWin(params)

    def openFile(self, event=False):
        files = [('Text Document', '*.txt')]
        file = askopenfile(filetypes=files, defaultextension=files)
        if file:
            with open(file.name, 'r') as txtFile:
                inParams        = txtFile.read()
            if not self.fiPath or not self.params:
                self.root.destroy()
            mainWins        .append(mainWin(inParams, file.name))

    class aHelp:
        """just a window containing the guide image"""
        def __init__(self, parent):
            global guideImgPath
            self.helpWin    = tk.Toplevel(parent.root)
            self.helpWin    .focus()
            self.helpWin    .title("Input Guide")
            self.helpWin    .iconbitmap(parent.icon)
            self.parent     = parent
            self.img        = tk.PhotoImage(master = self.helpWin,file=guideImgPath)
            self.wImg       = tk.Canvas(self.helpWin, width = 1200, height = 520)
            self.wImg       .create_image(0, 0, anchor = 'nw', image = self.img)
            self.wImg       .pack(side='left')
            self.helpWin     .bind("<Control-w>", self.close)
            self.helpWin    .mainloop()
        def close(self, event=None):
            self.helpWin.destroy()

    def makeAHelp(self):
        self.helpWins.append(self.aHelp(parent=self))

    def save(self, event=None):

        if self.fiPath:
            print(self.fiPath)
            values = eval(valuesSet)
            saveOut = ''.join([varNames[i] + " = " + str(values[i]) + "\n" for i in range(len(varNames))])[:-1]

            with open(self.fiPath, 'w') as outFile:
                outFile.write(saveOut)
        else:
            self.saveAs()

    def saveAs(self):
        values = eval(valuesSet)
        saveOut = ''.join([varNames[i] + " = " + str(values[i]) + "\n" for i in range(len(varNames))])[:-1]
        files = [('Text Document', '*.txt')]
        file = asksaveasfile(filetypes=files, defaultextension=files)
        if file:
            file.write(saveOut)
            self.fiPath     = file.name
            self.fiName     = self.fiPath.split('/')[-1].replace('.txt','')
            print(self.fiName)
            self.dirPath    = '/'.join(self.fiPath.split('/')[:-1])
            self.root       .title(self.fiName)

    class anOut:
        """an output window which performs calculations to generate images and displays responses (e.g. errors)"""

        def __init__(self, parent):
            self.done           = False                         #True when process() completes
            self.outFilePath    = None
            self.outWin         = tk.Toplevel(parent.root)
            self.outWin         .focus()
            self.outWin         .title("Output and Errors")
            self.outWin         .iconbitmap(parent.icon)
            self.parent         = parent
            self.responses      = parent.responses
            self.localTime      = '-'.join([str(i) for i in localtime()[0:3]])+' '+'.'.join([str(i) for i in localtime()[3:6]])

            self.txt            = tk.Text(self.outWin, width=100, height=20, bg='lightgray')
            self.txt            .pack(side='left', fill='both', expand='yes')

            self.txt_sb         = tk.Scrollbar(self.outWin, orient='vertical', command=self.txt.yview)
            self.txt_sb         .pack(side='right', fill='y')

            self.txt["yscrollcommand"] = self.txt_sb.set

            self.mb         = tk.Menu(self.outWin)
            self.mb_filem   = tk.Menu(self.mb, tearoff=0)
            self.mb_filem   .add_command(label="Save Error/Output", command=self.saveOut)
            self.outWin     .bind("<Control-s>", self.saveOut)
            self.mb_filem   .add_command(label="Save Error/Output as...", command=self.saveAsOut)
            self.mb         .add_cascade(label="File", menu=self.mb_filem)
            self.outWin     .config(menu=self.mb)
            self.outWin     .bind("<Control-w>", self.close)
            self.params      = self.parent.params
            self.responses   = ''
            self.exit        = False
            self.calc        = threading.Thread(target=self.process)
            self.calc        .start()
            self.outWin.protocol("WM_DELETE_WINDOW", self.close)
            self.displayResponse()
            self.outWin.mainloop()

        def close(self, event=False):
            self.exit = True
            self.outWin.destroy()

        def displayResponse(self, lastResponse=''):
            if self.responses != lastResponse:
                self.txt        .delete('1.0', 'end')
                self.txt        .insert('@0,0',   self.responses)
            if not self.done:
                self.txt        .after(50, self.displayResponse, self.responses)
            self.outWin     .update()

        def saveAsOut(self):
            output  = self.txt.get('1.0', 'end')
            files   = [('Text Document', '*.txt')]
            file    = asksaveasfile(filetypes=files, defaultextension=files)
            if file:
                file.write(output)
                self.outFilePath = file.name
                response = "\n\nsaved errors/outputs to {}".format(self.outFilePath)
                output(response, force=True)

        def saveOut(self, event=False):
            output = self.txt.get('1.0', 'end')

            if self.outFilePath:
                self.outWin.title(self.outFileName)
                with open(self.outFilePath, 'w') as outFile:
                    outFile.write(output)
            elif self.parent.dirPath:
                title               = "/ERRORS & OUTPUTS {} {}".format(self.parent.fiName, self.localTime)
                self.outFilePath    = self.parent.dirPath+title
                self.outFileName    = title[1:]
                self.outWin         .title(self.outFileName)

                with open(self.outFilePath+'.txt', 'w') as outFile:
                    outFile.write(output)
            else:
                self.saveAsOut()
            response = "\n\nsaved errors/outputs to {}".format(self.outFilePath)
            self.output(response, force=True)

        def process(self):
            # integers, non-zero decimals, and decimals
            self.done = False
            ints, dec, decnonz      = ['rowCount', 'trodesPerRow'], ['area','FAWidth','FAHeight','faMarkW', 'trodeLen', 'minMargin', 'LRMargin', 'TBMargin', 'yGapH', 'endYGapH', 'xGapW'], ['pixPerCm', 'sheetWidth', 'sheetHeight']
            params                  = self.params

            def testType(names, atype):
                """takes a set of variables and tests if it fits the type passed in, types: integer >=0, decimal >=0, decimal >0"""
                states = []
                responses = []
                for name in names:
                    item = params[name]

                    natype, test = atype.split(' ')[0], atype.split(' ')[1]
                    if item.capitalize() == 'False':
                        item = False
                    try:
                        if natype == 'integer':
                            changedItem = int(item)
                        elif natype == 'decimal':
                            changedItem = float(item)
                        # else: changedItem is not user input, so it will always be one or the other
                        state = eval(str(changedItem) + test)
                        params[name] = changedItem
                    except:
                        state = False
                    states.append(state)
                    if not state:
                        ifFalse = ''
                        if '=0' in atype:
                            ifFalse = ' or False\n'
                        response = name + ' must follow the rule: ' + atype + ifFalse
                        responses.append(response)
                return '\n\n'.join(responses)
            responses = testType(ints, 'integer >=0') + testType(decnonz, 'decimal >0')+ testType(dec, 'decimal >=0')
            if responses:
                self.output(responses)
                return None

            # auto variables
            def testMutuals():
                """tests if variables which can be set to None have the other variables (from which they will be calculated) NOT set to None
                trodeLen if not RowCount,
                    LRMargin/minMargin if not trodesPerRow,
                    rowCount and TBMargin if not trodeLen,
                    LRMargin and TBMargin if not minMargin,
                    minMargin if not LRMargin,
                    minMargin if not TBMargin"""

                #nonlocal params
                responses = []
                if not params['area'] and not (params['FAWidth'] and params['FAHeight']):
                    responses.append('if area is not provided, FAWidth and FAHeight must be provided.')
                if not params['FAWidth'] and not (params['area'] or params['FAHeight']):
                    responses.append('if FAWidth is not provided, area OR FAHeight must be provided.')
                if not params['FAHeight'] and not (params['area'] or params['FAWidth']):
                    responses.append('if FAHeight is not provided, area OR FAWidth must be provided.')
                if not params['rowCount'] and not params['trodeLen']:
                    responses.append('rowCount and/or trodeLen must be provided.')
                if not params['trodeLen'] and not (params['TBMargin'] or params['rowCount']):
                    responses.append('if trodeLen is not provided, (minMargin or TBMargin) and rowCount must be provided.')
                if not params['LRMargin'] and not params['minMargin']:
                    responses.append('if LRMargin is not provided, minMargin must be provided.')
                elif not params['LRMargin'] and params['minMargin']:
                    params['LRMargin'] = params['minMargin']
                if not params['TBMargin'] and not params['minMargin']:
                    responses.append('if TBMargin is not provided, minMargin must be provided.')
                elif not params['TBMargin'] and params['minMargin']:
                    params['TBMargin'] = params['minMargin']
                if not params['trodesPerRow'] and not params['LRMargin']:
                    responses.append('if trodesPerRow is not provided, minMargin and/or LRMargin must be provided.')

                return '\n\n'.join(responses)
            responses = testMutuals()
            if responses:
                self.output(responses)
                return None

            bridgeLen       = 0.094  # height of bridges between rows to which trodes are vertically attached
            bridgePxLen     = intr(bridgeLen * params['pixPerCm'])  # above in pixels

            faMarkW         = params['faMarkW']  # len of nic separating functional params['area'] from rest of trode
            faMarkPxW       = intr(faMarkW   * params['pixPerCm'])  # above in px

            lRMarginPxLen   = intr(params['pixPerCm'] * params['LRMargin'])
            tBMarginPxLen   = intr(params['pixPerCm'] * params['TBMargin'])
            totalPxHeight   = intr(params['pixPerCm'] * params['sheetWidth'])  # height of entire canvas in pixels
            totalPxWidth    = intr(params['pixPerCm'] * params['sheetHeight'])  # width  of above
            print('h', totalPxHeight)
            print('w', totalPxWidth)
            usableHeight    = (totalPxHeight - (2 * tBMarginPxLen) - 4)  # height in px of cutable params['area'] between top and bottom margins
            usableWidth     = (totalPxWidth - (2 * lRMarginPxLen) - 4)  # width  in px of cutable params['area'] between left and right margins

            endYGapHPx      = intr(params['endYGapH'] * params['pixPerCm'])  # px len of gaps in far left and right outlines of trode row
            yGapHPx         = intr(params['yGapH'] * params['pixPerCm'])  # px len of gaps in every edge /between/ electrodes
            xGapWPx         = intr(params['xGapW'] * params['pixPerCm'])  # px len of horizontal link at bottom of trodes

            white           = np.array([255]).astype(np.uint8)  # value for a white pixel which array points to before image is generated
            black           = np.array([0]).astype(np.uint8)  # above for a black pixel

            def calcFalses():
                """calculates variables which were input as False"""
                width, height, area = params['FAWidth'], params['FAHeight'], params['area']
                #least likely scenario that both are given. tested implicitly.

                if not (width or height):                         #if neither are given, most common scenario
                    width  = sqrt(area)
                    height = width
                elif not width:                                   #if only height given, 2nd most common
                    width  = area / height
                elif not height:                                  #if only width given, 2nd most common
                    height = area / width

                pxWidth = intr(width * params['pixPerCm'] + 2)  # width (of FA) in pixels. Has to be either returned or recalculated and i chose to recalculate for neatness

                if params['trodeLen']:
                    trodePxLen          = intr(params['trodeLen'] * params['pixPerCm'] + 4)  # length of electrode in px

                if not params['trodeLen']:  # if electrode length is not provided its calculated from row number
                    trodePxLen          = (usableHeight - ((params['rowCount'] - 1) * bridgePxLen)) // params['rowCount']
                    params['trodeLen']  = (trodePxLen - 4) / params['pixPerCm']  # length of electrode in px

                elif not params['rowCount']:  # if row count is not provided it's calculated from electrode length and usableHeight
                    trodePxLen          = intr(params['trodeLen'] * params['pixPerCm'] + 4)  # length of electrode in px
                    params['rowCount']  = (usableHeight + bridgePxLen) // (trodePxLen + bridgePxLen)  # bridge is added to usable height since bridgenum = rownum-1

                if not params['trodesPerRow']:  # if rowLen (trodes per row) is not provided, it's calculated from trode with and usableWidth
                    params['trodesPerRow'] = usableWidth // (pxWidth + 2)

                return trodePxLen, width, height

            trodePxLen, width, height      = calcFalses()                   #length of electrode in pixels
            pxWidth         = intr(width * params['pixPerCm'] + 2)           # width (of FA) in pixels
            pxHeight        = intr(height * params['pixPerCm'] + 2)          # height (of FA) in pixels
            rowPxHeight     = trodePxLen + bridgePxLen                      #total height of a row including bridge
            nfLenPx         = trodePxLen - pxHeight                         #non-functional length, used for calculating positions of gaps
            nfLen           = nfLenPx / params["pixPerCm"]

            def checkGaps():
                responses = []
                maxYGapH    = round(0.3*nfLen, 3)
                if params["endYGapH"] > nfLen:
                    responses.append("endYGapH is too large for trodeLen and (area or FAHeight)\n\tmax {} cm for selected trodeLen of {} cm and calculated FAHeight of {} cm.".format(nfLen, params["trodeLen"], height))
                    if params["endYGapH"] != 0.044:
                        responses.append("\tConsider using default value of 0.044 cm.")
                    else:
                        responses.append("\tTry modifying trodeLen, area, or FAHeight.")

                if params["yGapH"] > maxYGapH:
                    responses.append("YGapH is too large for trodeLen and (area or FAHeight)\n\tmax {} cm for selected trodeLen of {} cm and calculated FAHeight of {} cm.".format(maxYGapH, params["trodeLen"], height))
                    if params["yGapH"] != 0.036:
                        responses.append("\tConsider using the default value of 0.036 cm.")
                    else:
                        responses.append("\tTry modifying trodeLen, area, or FAHeight.")

                if params["xGapW"] > width:
                    responses.append("xGapW is too large for (area or FAWidth) \n\tmaximum gap width is total width, which was calculated as {} cm.\n\tConsider using default value of 0.036 cm.".format(width))
                if params["faMarkW"] > width:
                    response = "faMarkW is too large for (area or FAWidth)\n\tmaximum marker length is total width, which was calculated as {} cm^2\n(this would cut your functional area OFF of your electrodes)".format(width)
                    if width > 0.252:
                        response += "\tConsider using the default value of 0.126 cm."
                    responses.append(response)
                return '\n'.join(responses)

            responses = checkGaps()

            if responses:
                self.output(responses)
                return None

            def testTotals():

                responses = []
                summedWidth = usableWidth - abs((params['trodesPerRow'] * pxWidth))
                if summedWidth < 0:
                    response = "trodesPerRow, (minMargin or LRMargin), and (area of FAWidth) are too large for size of carbon paper.\n\tDecrease LRMargin or trodesPerRow, try setting trodesPerRow = False."
                    responses.append(response)
                summedHeight = usableHeight - abs((trodePxLen * params['rowCount'])) - abs((bridgePxLen * (params['rowCount'] - 1)))
                if summedHeight < 0:
                    response = "rowCount, trodeLen, and (minMargin or TBMargin) are too large for size of carbon paper.\n\tdecrease TBMargin, rowCount, or trodeLen or set rowCount or trodeLen = False"
                    responses.append(response)
                if params['xGapW'] > width:
                    response = "xGapW cannot exceed electrode width ({} given provided area or FAWidth values.)".format(width)
                    responses.append(response)
                return '\n\n'.join(responses)

            responses = testTotals()
            if responses:
                self.output(responses)
                return None

            def calcTrode(parent, termini=False, leftTrode = False, rightTrode = False):
                """calculates idexes of points which must be colored, if termini == True then only leftmost and rightmost edges are generated
                if leftTrode or rightTrode are True, then requested trode is leftmost or rightmost so its left or right edge are omitted and subsequently calculated when
                this function is called with termini=True"""
                px, py = parent  # parent     x, y values
                ox, oy = px + pxWidth - 1, py + trodePxLen  # opposite   x, y values relative to one electrode
                mx, my = px + pxWidth - faMarkPxW  , py + pxHeight + 1  # mark       x, y values, horizontal line labeling funct params['area']

                if termini:  # generate ONLY far left and right edges of the row
                    ox          = px + (pxWidth * params['trodesPerRow'])                   # this time ox is x of opposite edge of trode row, not of trode
                    termLnkE    = oy - intr(0.5 * nfLenPx)                                   # y value of End of linker on far left and right edges of the row
                    termLnkB    = termLnkE - endYGapHPx                                     # y value of Beginning  of above
                    termLinks   = [y for y in range(termLnkB, termLnkE)]                    # y positions of pixels of above
                    left        = [[px + 1, y] for y in range(py, oy, 1) if y not in termLinks] \
                                + [[px, y] for y in range(py, oy, 1) if y not in termLinks]  # far left  edge of row
                    right       = [[ox, y] for y in range(py, oy, 1) if y not in termLinks] \
                                + [[ox + 1, y] for y in range(py, oy, 1) if y not in termLinks]  # far right edge of row
                    points      = left + right

                else:
                    lyEs = [oy - (intr((i + 1) / 4 * nfLenPx)) for i in range(3)]               # gap END y values of inter-trode links
                    lyBs = [gye - yGapHPx for gye in lyEs]                                      # gap BEGINNING y values of inter-trode links
                    lys  = [[i for i in range(lyBs[p], lyEs[p] + 1)] for p in range(len(lyEs))]  # every pixel of inter-trode links generated from above termini
                    lys  = [y for lis in lys for y in lis]                                       # merge sublists of above

                    lxb = (px + (pxWidth // 2) - (xGapWPx // 2))
                    lxe = (px + (pxWidth // 2) + (xGapWPx // 2))               # beginning and end of x-axis linkers tween trode and bridge
                    lxs = [x for x in range(lxb, lxe, 1)]                      # every pixel in above

                    top     = [[x, py] for x in range(px, ox, 1)] \
                            + [[x, py + 1] for x in range(px, ox, 1)]  # pixels in top    line of trode
                    bottom  = [[x, oy - 1] for x in range(px, ox + 1, 1) if x not in lxs] \
                            + [[x, oy - 2] for x in range(px, ox, 1) if x not in lxs]  # pixels in bottom line of trode
                    left    = [[px, y] for y in range(py, oy, 1) if y not in lys]  # ...       left   line of trode
                    right   = [[ox, y] for y in range(py, oy, 1) if y not in lys]  # ...       right  line of trode
                    marker  = [[x, my] for x in range(mx, ox, 1)] \
                            + [[x, my - 1] for x in range(mx, ox,1)]  # ...       line separating FA from rest of trode

                    if leftTrode:
                        points = top + bottom + right + marker
                    elif rightTrode:
                        points = top + bottom + left + marker
                    else:
                        points = top + bottom + left + right + marker
                return points

            def draw(canvas, points):
                for i, point in enumerate(points):
                    x, y = point[0], point[1]
                    canvas[y, x] = black

                return canvas

            def calcEdge():
                """generates 2 px perimeter in cut file for positioning"""
                top     = [[x, 0] for x in range(totalPxWidth)]                 + [[x, 1] for x in range(totalPxWidth)]
                bottom  = [[x, totalPxHeight - 1] for x in range(totalPxWidth)] + [[x, totalPxHeight - 2] for x in range(totalPxWidth)]
                left    = [[0, y] for y in range(totalPxHeight)]                + [[1, y] for y in range(totalPxHeight)]
                right   = [[totalPxWidth - 1, y] for y in range(totalPxHeight)] + [[totalPxWidth - 2, y] for y in range(totalPxHeight)]
                points = top + bottom + left + right
                print(top[0],top[-1],bottom[0],bottom[-1],left[0],left[-1],right[0],right[-1])
                return points

            def createCanvas():
                """creates a white canvas on which to draw,  with perimeter from edge()"""
                # row         = [white for x in range(totalPxWidth)]
                # canvas      = np.array([row.copy() for y in range(totalPxHeight)])
                canvas = np.full([totalPxHeight, totalPxWidth, 3], white, dtype=np.uint8)
                print('tph', totalPxHeight, 'tpw', totalPxWidth)
                edgePx = calcEdge()
                canvas = draw(canvas, edgePx)
                return canvas

            canvas = createCanvas()

            def createRow(px, py):
                """takes coordinates of parent pixel (upper left pixel in row) and generates pixels for entire row of trodes"""
                points = []
                for i in range(params['trodesPerRow']):
                    tpx = px + (i * pxWidth) + 1
                    if i == 0:
                        points += calcTrode([tpx, py], leftTrode=True)
                    elif i == params['trodesPerRow']-1:
                        points += calcTrode([tpx, py], rightTrode=True)
                    else:
                        points += calcTrode([tpx, py])

                points += calcTrode([px, py], True)
                return points

            px          = lRMarginPxLen  #parent x value

            #if an input file is selected, output directory made with same name, else its stored in cache until
            #program succeeds, when openFile is called requesting parameters to be saved,
            #then a directory is made using same name, cache transfered here, and deleted.

            if self.parent.dirPath:
                dirName     = self.parent.dirPath + r"/{} {}".format(self.parent.fiName, self.localTime)
            else:
                dirName     = ACdir + r"/caches/cache {}".format(self.localTime)

            if not os.path.exists(dirName):
                os.makedirs(dirName)
            def drawRow(rowNum):
                if self.exit:
                    return None
                py          = tBMarginPxLen + (rowNum * rowPxHeight)
                row         = createRow(px, py)
                drawnRow    = draw(deepcopy(canvas), row)

                img         = PIMG.fromarray(drawnRow)  # convert to image
                fileName    = r"\{}cm2 {}cm row {}.png".format(round(params['area'], 2), round(params['trodeLen'], 2), rowNum + 1)
                img         .save(dirName + fileName)

                del row, drawnRow, img, fileName
            for rowNum in range(params['rowCount']):
                if self.parent.rowThread:
                    threading.Thread(target=drawRow, args = [rowNum]).start()
                else:
                    drawRow(rowNum)
            if self.exit:
                return None
            if not self.parent.dirPath:
                self.parent .saveAs()
                if self.parent.dirPath:
                    newDir      = self.parent.dirPath + r"/{} {}".format(self.parent.fiName, self.localTime)
                    shutil      .copytree(dirName, newDir)
                    shutil      .rmtree(ACdir + r"/caches")
                    dirName     = newDir
                else:
                    shutil.rmtree(dirName)
                    response = "\nNo output directory selected. Aborting process."
                    self.output(response)
                    return None

            response = ("\nprocess complete","\ncutting images output in:\n", dirName)
            open_folder(dirName)
            self.done = True
            self.output(response)

        def output(self, response, force=False):
            """converts a print-like list to a string, prints and outputs it in outWin"""
            if type(response) in [list, tuple]:
                response = ' '.join([str(i) for i in response])
            print(response)
            self.responses += response
            if force:
                self.displayResponse()

    def makeAnOut(self):
        values = eval(valuesSet)
        for i, varName in enumerate(varNames):
            self.params[varName] = values[i]
        del self.outWins
        self.outWins = []
        self.outWins.append(self.anOut(parent=self))

    def makeAnErr(self, message):
        self.erWins.append(self.anEr(parent = self, message = message))
        print(self.erWins)

mainWin(default)
