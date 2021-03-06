#-*-codin:utf-8-*-
import os
import wx
import wx.grid
from wx.lib.wordwrap import wordwrap
from wx.tools import img2py
import tempfile
from wx.tools.img2py import img2py
from wx.lib.embeddedimage import PyEmbeddedImage
try:
    import agw.flatnotebook as FNB
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.flatnotebook as FNB
    
from collections import OrderedDict
from xml.dom import minidom
from imagesource import pe, add_butt_img, TheCrackOfDawn

class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self,None, title="PE VISUALER",size=(500,500))
        self.SetIcon(pe.getIcon())  
        self.sp = wx.SplitterWindow(self)
        self.pe_tree = PETreeCtrl(self.sp, self)
        self.pe_infos = FNB.FlatNotebook(self.sp)
        self.pe_infos.Hide()
        self.sp.Initialize(self.pe_tree)
        
class PETreeCtrl(wx.TreeCtrl):
    def __init__(self, parent, frame):
        self.tree_info = {}
        wx.TreeCtrl.__init__(self, parent)
        self.main_frame = frame
        self.popup_menu = wx.Menu()
        show_details = self.popup_menu.Append(-1, 'show details')
        self.Bind(wx.EVT_MENU, self.OnShowDetails, show_details)
        rebuild = self.popup_menu.Append(-1, 'build new view')
        self.Bind(wx.EVT_MENU, self.rebuild, rebuild)
        add_nodes = self.popup_menu.Append(-1, 'add nodes')
        self.Bind(wx.EVT_MENU, self.add_nodes, add_nodes)
        del_node = self.popup_menu.Append(-1, 'delete node')
        self.Bind(wx.EVT_MENU, self.DelNode, del_node)
        edit_node = self.popup_menu.Append(-1, 'edit node')
        self.Bind(wx.EVT_MENU, self.EditNode, edit_node)
        load_from_xml = self.popup_menu.Append(-1, 'load from...')
        self.Bind(wx.EVT_MENU, self.parser, load_from_xml)
        save_as_xml = self.popup_menu.Append(-1, 'save to...')
        self.Bind(wx.EVT_MENU, self.saver, save_as_xml)
        about = self.popup_menu.Append(-1, 'about')
        self.Bind(wx.EVT_MENU, self.OnAbout, about)
        
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelection)
        
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnShowPopup)
        
    def DelNode(self, event):
        dlg = wx.MessageDialog(None, 'Are you sure to delete it?', 'warning', wx.YES_NO|wx.ICON_WARNING)
        if dlg.ShowModal() == wx.ID_YES:
            nid = self.GetSelection()
            self.Delete(nid)
        dlg.Destroy()
        
    def EditNode(self, event):
        def img_to_str(img):
            file = tempfile.mktemp(dir='')
            img2py(img, file)
            content = open(file, 'r').read()
            if os.path.exists(file):
                os.remove(file)
            img = eval(content[content.find('=')+1:])
            return img.data
        
        nid = self.GetSelection()
        if not nid:return
        dlg = EditDialog(self, nid)
        if dlg.ShowModal() == wx.ID_OK:
            row_num = dlg.grid.GetNumberRows()
            new_attrs = OrderedDict()
            self.SetItemText(nid, dlg.grid.GetCellValue(0, 0))
            for i in range(1, row_num):
                if dlg.grid.GetCellValue(i, 0):
                    if dlg.grid.GetCellValue(i, 2) == 'img':
                        img = dlg.grid.GetCellValue(i, 1)
                        new_attrs[dlg.grid.GetCellValue(i, 0)] = {'value':dlg.image_data[i],
                                                              'type':'img'}
                    elif dlg.grid.GetCellValue(i, 2) == 'img-new':
                        path = dlg.grid.GetCellValue(i, 1)
                        img = img_to_str(path)
                        new_attrs[dlg.grid.GetCellValue(i, 0)] = {'value':img,
                                                              'type':'img'}
                    else:
                        new_attrs[dlg.grid.GetCellValue(i, 0)] = {'value':dlg.grid.GetCellValue(i, 1),
                                                              'type':dlg.grid.GetCellValue(i, 2)}
            self.SetPyData(nid, new_attrs)
        dlg.Destroy()
        
    def OnSelection(self, event):
        id = event.GetItem()
        page_num = self.main_frame.pe_infos.GetPageCount()
        self.main_frame.pe_infos.DeleteAllPages()
        self.main_frame.pe_infos.AddPage(InfoPanel(self.main_frame.pe_infos, self.GetPyData(id)), 'info')
        #FNB.FlatNotebook.GetPage(page)
    
    def OnShowPopup(self, event):
        pos = event.GetPosition()
        item = self.popup_menu.FindItemByPosition(0)
        if self.main_frame.sp.IsSplit():
            item.SetText('hide details')
        else:
            item.SetText('show details')
        self.PopupMenu(self.popup_menu, pos)
        
        
    def parser(self, event):
        if isinstance(event, str):
            self.DeleteAllItems()
            xml_path = event
        else:
            dlg = wx.FileDialog(None, 'save to', '', '', 'xml(*.xml)|*.xml')
            if dlg.ShowModal() == wx.ID_OK:
                xml_path = dlg.GetPath()
                self.DeleteAllItems()
            else:
                dlg.Destroy()
                return
            dlg.Destroy()
            
        try:
            dom = minidom.parse(xml_path)
        except Exception, err:
            wx.MessageBox('somethong is wrong while parsing the xml: %s'%err.message,  'sorry', wx.ICON_ERROR)
            return
        #add first element
        root_elem = dom.documentElement
        root_node = self.AddRoot(root_elem.nodeName)
        #elem_attrs = dict(root_elem.attributes.items())
        #self.SetPyData(root_node, dict(root_elem.attributes.items()))
        class agent:pass
        elem_agent = agent()
        elem_agent.childNodes = [root_elem]
        new_add = {root_node:elem_agent}
        while new_add:
            added = {}
            for node, elem in new_add.items():
                for elemc in elem.childNodes:
                    if elemc.firstChild and elemc.firstChild.nodeType == 3:
                        continue
                    attrs = []
                    for elemcc in elemc.childNodes:
                        if elemcc.firstChild and elemcc.firstChild.nodeType == 3:
                            elem_attrs = dict(elemcc.attributes.items())
                            if 'type' in elem_attrs:
                                attrs.append((elemcc.nodeName, {'value':elemcc.firstChild.nodeValue,\
                                                                 'type':elem_attrs['type']}))
                            else:
                                attrs.append((elemcc.nodeName, {'value':elemcc.firstChild.nodeValue,\
                                                                 'type':'txt'}))
                    if isinstance(elem, agent):
                        nodec = root_node
                    else:   
                        nodec = self.AppendItem(node,elemc.nodeName)
                    if not attrs:attrs.append(('nothing', {'type':'txt', 'value':' '}))
                    self.SetPyData(nodec, OrderedDict(attrs))
                    added[nodec] = elemc
    
                    
            new_add = added
        
    def saver(self, event):
        dlg = wx.FileDialog(None, 'save to', '', '', 'xml(*.xml)|*.xml', style=wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            xml_path = dlg.GetPath()
        else:
            dlg.Destroy()
            return 
        dlg.Destroy()
        dim = minidom.getDOMImplementation()
        root_node = self.GetRootItem()
        if not root_node: return 
        dom = dim.createDocument(None, self.GetItemText(root_node), None)
        root_elem = dom.documentElement
        #for name, value in self.GetPyData(root_node).items():
        #    root_elem.setAttribute(name, value)
        for name, value in self.GetPyData(root_node).items():
            text_elem = dom.createElement(name)
            text = dom.createTextNode(value['value'])
            text_elem.setAttribute('type', value['type'])
            text_elem.appendChild(text)
            root_elem.appendChild(text_elem)
        new_add = {root_node:root_elem}
        while new_add:
            added = {}
            for node, elem in new_add.items():
                nodec, cookie = self.GetFirstChild(node)
                while nodec:
                    elemc = dom.createElement(self.GetItemText(nodec))
                    elem.appendChild(elemc)
                    for name, value in self.GetPyData(nodec).items():
                        text_elem = dom.createElement(name)
                        text = dom.createTextNode(value['value'])
                        text_elem.setAttribute('type', value['type'])
                        text_elem.appendChild(text)
                        elemc.appendChild(text_elem)
                    added[nodec] = elemc  
                    nodec, cookie = self.GetNextChild(node, cookie)
            new_add = added
        open(xml_path, 'w').write(dom.toxml(encoding='utf-8'))
    
    def rebuild(self, event):
        dialog = AddDialog(self, 'build a new tree')
        status = dialog.ShowModal()
        if status == wx.ID_OK:
            self.DeleteAllItems()
            nodes = dialog.nodes
            if len(nodes) == 0:
                wx.MessageBox('please add a root node', 'error', wx.ICON_ERROR)
                dialog.Destroy()
                return
            node  = nodes.keys()[0]
            rid = self.AddRoot(node)
            self.SetPyData(rid, nodes[node])
        dialog.Destroy()
    
    def add_nodes(self, event): 
        itid = self.GetSelection()
        if not itid:
            wx.MessageBox('please select a parent node', 'error', wx.ICON_ERROR)
            return
        dialog = AddDialog(self, 'add a node')
        status = dialog.ShowModal()
        if status == wx.ID_OK:
            nodes = dialog.nodes
            if len(nodes) == 0:
                wx.MessageBox('please input a node you want to add', 'error', wx.ICON_ERROR)
                dialog.Destroy()
                return
            for node in nodes:
                id = self.AppendItem(itid, node)
                self.SetPyData(id, nodes[node])
        dialog.Destroy()
                
    def OnShowDetails(self, event):
        if self.main_frame.sp.IsSplit():
            self.main_frame.pe_infos.Hide()
            self.main_frame.sp.Unsplit()
        else:
            self.main_frame.pe_infos.Show()
            self.main_frame.sp.SplitHorizontally(self.main_frame.pe_tree, self.main_frame.pe_infos, -100)
    
    def OnAbout(self, event):
        # First we create and fill the info object
        painter = self
        info = wx.AboutDialogInfo()
        info.SetIcon(TheCrackOfDawn.getIcon())
        info.Name = "PE Visualer"
        info.Version = "1.0"
        info.Copyright = "(c) cd"
        info.Description = wordwrap(
            "This tool try to make a file format visible in a simple way."
            "I met some problems while learning PE format. There are so many details that i can't remember."
            "It's also hard for me to remain a global view while i'm struggling in details."
            "So, i write this. For now, it meets my need perfectly. So no more time will be paid."
            "If you have any need, you are free to change or ever rewrite it.",
            350, wx.ClientDC(painter))
        info.WebSite = ("https://github.com/thecrackofdawn/PE-Visualer", "PE Visualer's source code")
        info.Developers = ["weibo : TheCrackOfDawn",
                           "hoping more and more attention ^_^"]
        licenseText = "MIT. You are free to do whatever you want."
        info.License = wordwrap(licenseText, 500, wx.ClientDC(painter))

        # Then we call wx.AboutBox giving it that info object
        wx.AboutBox(info)
    
class AddDialog(wx.Dialog):
    def __init__(self, parent, caption):
        wx.Dialog.__init__(self, parent, -1, caption, size=(450, 320))
        
        self.nodes = OrderedDict()
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        add_panel = wx.Panel(self)
        add_sizer = wx.BoxSizer(wx.VERTICAL)
        stbox = wx.StaticBox(add_panel, -1, 'node name')
        stbox_sizer = wx.StaticBoxSizer(stbox, wx.VERTICAL)
        #stbox_sizer.Add(wx.StaticText(add_panel, -1, 'node name'), 0, wx.ALL,10)
        self.node_name = wx.TextCtrl(add_panel, -1)
        stbox_sizer.Add(self.node_name, 0, wx.ALL,10)
        add_sizer.Add(stbox_sizer, flag=wx.ALIGN_CENTER_HORIZONTAL)
        
        stbox = wx.StaticBox(add_panel, -1, 'attribute')
        stbox_sizer = wx.StaticBoxSizer(stbox, wx.VERTICAL)
        stbox_sizer.Add(wx.StaticText(add_panel, -1, 'name'))
        choices = ['name', 'size', 'description', 'add new']
        panel = wx.Panel(add_panel)
        self.attr = wx.Choice(panel, -1, choices=choices, pos=(0, -1))  
        self.new_attr = wx.TextCtrl(panel, -1, size=(80, -1), pos=(95, -1))
        self.new_attr.Disable()
        stbox_sizer.Add(panel)
        self.Bind(wx.EVT_CHOICE, self.OnChoice, self.attr)
        stbox_sizer.Add(wx.StaticText(add_panel, -1, 'value'))
        panel = wx.Panel(add_panel)
        self.value = wx.TextCtrl(panel, -1, style=wx.TE_MULTILINE)
        self.is_img = wx.CheckBox(panel, -1, 'image', pos=(130, 10))
        self.Bind(wx.EVT_CHECKBOX, self.OnImg, self.is_img)
        stbox_sizer.Add(panel)
        bmp = add_butt_img.GetBitmap()
        add_butt = wx.BitmapButton(add_panel, -1, bmp)
        self.Bind(wx.EVT_BUTTON, self.OnAddButt, add_butt)
        
        stbox_sizer.Add(add_butt, flag=wx.ALIGN_CENTER_HORIZONTAL)
        add_sizer.Add(stbox_sizer, flag=wx.ALIGN_CENTER_HORIZONTAL)
         
        
        
        panel = wx.Panel(add_panel)
        okButton = wx.Button(panel, wx.ID_OK, 'OK', pos=(30, 10), size=(50, -1))
        cancelButton = wx.Button(panel, wx.ID_CANCEL, 'cancel', pos=(110, 10), size=(50, -1))
        add_sizer.Add(panel)
        
        add_panel.SetSizer(add_sizer)
        add_panel.FitInside()
        
        self.info = wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_RICH2)
        self.info.SetEditable(False)
        self.nodes_pos = {}
        sizer.Add(add_panel, 3, flag=wx.EXPAND)
        sizer.Add(self.info, 4, flag=wx.EXPAND)
        
        
        self.SetSizer(sizer)
        self.FitInside()
        
    def OnChoice(self, event):
        select = event.GetString()
        if select == 'add new':
            self.new_attr.Enable()
        else:
            self.new_attr.Disable()
            
    def OnImg(self, event):
        if not self.is_img.GetValue():
            return 
        dlg = wx.FileDialog(None)
        if dlg.ShowModal() == wx.ID_OK:
            self.value.SetValue(dlg.GetPath())
        else:
            self.is_img.SetValue(False)
        dlg.Destroy()
    
    def OnAddButt(self, event):
        invaild_item = None
        node_name = self.node_name.GetValue()
        if not node_name:
            wx.MessageBox('please input the name of the node', 'error',  wx.ICON_ERROR)
            return 
        attr_name = self.attr.GetStringSelection()
        if attr_name == 'add new': attr_name = self.new_attr.GetValue()
        if not attr_name :
            wx.MessageBox('please input the name of the attribute', 'error', wx.ICON_ERROR)
            return
        """
        if node_name in self.nodes and attr_name in self.nodes[node_name]:
            wx.MessageBox('attribute exists...', 'error', wx.ICON_ERROR)
            return 
        """
        
        def add_text(node_name, text):
            self.info.SetInsertionPoint(self.nodes_pos[node_name][1])
            self.info.WriteText(text)
            self.nodes_pos[node_name][1] += len(text)
            
        def img_to_str(img):
            file = tempfile.mktemp(dir='')
            img2py(img, file)
            content = open(file, 'r').read()
            if os.path.exists(file):
                os.remove(file)
            img = eval(content[content.find('=')+1:])
            return img.data
            
        if not node_name in self.nodes:
            self.nodes[node_name] = OrderedDict()
        self.nodes[node_name][attr_name] = {}
        if self.is_img.GetValue():
            self.nodes[node_name][attr_name]['value'] = img_to_str(self.value.GetValue())
            self.nodes[node_name][attr_name]['type'] = 'img' 
        else:
            self.nodes[node_name][attr_name]['value'] = self.value.GetValue() if self.value.GetValue() else ' '
            self.nodes[node_name][attr_name]['type'] = 'txt' 
        self.info.Clear()
        showpos = 0
        for name in self.nodes:
            pos = self.info.LastPosition
            self.info.AppendText('\n'+name+'\n')
            f = wx.Font(20, wx.DEFAULT, wx.NORMAL, wx.BOLD)
            self.info.SetStyle(pos, self.info.LastPosition, wx.TextAttr('white', 'black', f))
            for attr in self.nodes[name]:
                pos = self.info.LastPosition
                if attr == attr_name and name == node_name:
                    showpos = pos
                self.info.AppendText(attr+'\n')
                f = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)
                self.info.SetStyle(pos, self.info.LastPosition, wx.TextAttr('white', 'gray', f))
                if self.nodes[name][attr]['type']  == 'img':
                    self.info.AppendText('an image file...')
                else:
                    self.info.AppendText(self.nodes[name][attr]['value']+'\n')
        if showpos: self.info.ShowPosition(showpos-1)
        
        #clean
        self.new_attr.Clear()
        self.value.Clear()
        self.is_img.SetValue(False)
   
class EditDialog(wx.Dialog):
    def __init__(self, parent, nid):
        wx.Dialog.__init__(self, None)
        self.SetMinSize((500, 400))
        self.SetMaxSize((1000, 800))
        self.parent = parent
        self.nid = nid
        attrs = self.parent.GetPyData(nid)
        row_num = len(attrs) + 1
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.grid = wx.grid.Grid(self, -1)
        self.grid.CreateGrid(row_num, 4)
        self.grid.SetDefaultRenderer(wx.grid.GridCellEnumRenderer())
        self.grid.SetDefaultEditor(wx.grid.GridCellAutoWrapStringEditor())
        self.grid.HideColLabels()
        self.grid.HideRowLabels()
        name = self.parent.GetItemText(nid)
        self.grid.SetCellSize(0, 0, 1, 4)
        self.grid.SetCellValue(0, 0, name)
        self.grid.SetCellAlignment(0, 0, wx.ALIGN_LEFT, wx.ALIGN_CENTRE)
        self.grid.SetCellBackgroundColour(0, 0, 'gray')
        self.grid.GetGridWindow().Bind(wx.EVT_LEFT_DOWN, self.OnClick)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnDoubleClick)
        self.image_data = {}
        row = 1
        for name, value in attrs.items():
            self.grid.SetCellValue(row, 0, name)
            if value['type'] == 'img':
                self.grid.SetCellValue(row, 2, value['type'])
                self.grid.SetCellValue(row, 1, 'this is an image...')
                self.image_data[row] = value['value']
                self.grid.SetReadOnly(row, 1)          
            else:
                self.grid.SetCellValue(row, 2, value['type'])
                self.grid.SetCellValue(row, 1, value['value'])
            self.grid.SetCellRenderer(row, 3, ButtonRenderer('delete'))
            self.grid.SetReadOnly(row, 2)
            self.grid.SetReadOnly(row, 3)
            row += 1
        self.grid.AutoSize()
        self.grid.SetSize(self.GetSize())
        sizer.Add(self.grid, 1, wx.EXPAND)
        panel = wx.Panel(self)
        okButton = wx.Button(panel, wx.ID_OK, 'OK', pos=(30, 10), size=(50, -1))
        addButton = wx.Button(panel, -1, 'add', pos=(80, 10), size=(50, -1))
        self.Bind(wx.EVT_BUTTON, self.OnAdd, addButton)
        cancelButton = wx.Button(panel, wx.ID_CANCEL, 'cancel', pos=(130, 10), size=(50, -1))
        sizer.Add(panel, flag=wx.CENTER)
        self.SetSizer(sizer)
        self.Fit()
        
        
    def OnAdd(self, event):
        dlg = AddAttrDialog()
        if dlg.ShowModal() == wx.ID_OK:
            self.grid.AppendRows(1)
            row = self.grid.GetNumberRows() - 1
            self.grid.SetCellValue(row, 2, dlg.type.GetStringSelection())
            if 'img' in dlg.type.GetStringSelection():
                self.grid.SetReadOnly(row, 1)
            self.grid.SetReadOnly(row, 2)
            self.grid.SetReadOnly(row, 3)
            self.grid.SetCellRenderer(row, 3, ButtonRenderer('delete'))
            self.grid.AutoSize()
            self.grid.SetSize(self.GetSize())
        dlg.Destroy()
        
        
    def OnClick(self, event):
        x, y = self.grid.CalcUnscrolledPosition(event.GetX(), event.GetY())
        coords = self.grid.XYToCell(x, y)
        row = coords[0]
        col = coords[1]
        if isinstance(self.grid.GetCellRenderer(row, col), ButtonRenderer):
            rect = self.grid.GetCellRenderer(row, col).butt_rect
            if x >= rect.x and x <= rect.x+rect.width and \
                y>=rect.y and y<=rect.y+rect.height:
                dlg = wx.MessageDialog(None, 'Are you sure to delete it?', 'warning', wx.YES_NO|wx.ICON_WARNING)
                if dlg.ShowModal() == wx.ID_YES:
                    self.grid.DeleteRows(row, 1)
                dlg.Destroy()
            else:
                event.Skip()
        else:
            event.Skip()
        
    def OnDoubleClick(self, event):
        row = event.GetRow()
        col = event.GetCol()
        if col == 1 and 'img' in self.grid.GetCellValue(row, 2).strip():
            dlg = wx.FileDialog(None)
            if dlg.ShowModal() == wx.ID_OK:
                self.grid.SetCellValue(row, col, dlg.GetPath())
                self.grid.SetCellValue(row, 2, 'img-new')
                self.grid.AutoSize()
                self.grid.ForceRefresh()
            dlg.Destroy()
        else:
            event.Skip()
            
class AddAttrDialog(wx.Dialog):
    def __init__(self):
        super(AddAttrDialog, self).__init__(None)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.type = wx.RadioBox(self, -1, 'type', choices=['txt', 'img'])
        sizer.Add(self.type, 1, wx.EXPAND)
        panel = wx.Panel(self)
        wx.Button(panel, wx.ID_OK, 'ok', pos=(0, 5), size=(40, -1))
        wx.Button(panel, wx.ID_CANCEL, 'no', pos=(50, 5), size=(40, -1))
        sizer.Add(panel, 1, flag=wx.CENTER)
        self.SetSizer(sizer)
        self.Fit()
             
class InfoPanel(wx.grid.Grid):
    def __init__(self, parent, info_dict):
        wx.grid.Grid.__init__(self, parent)
        self.CreateGrid(0, 1)
        self.SetDefaultRenderer(wx.grid.GridCellEnumRenderer())
        self.SetDefaultEditor(wx.grid.GridCellAutoWrapStringEditor())
        self.HideColLabels()
        for info in info_dict:
            self.AppendRows(1)
            rnum = self.GetNumberRows() -1
            self.SetRowLabelValue(rnum, info)
            font = self.GetCellFont(rnum, 0)
            if isinstance(info_dict[info], dict):
                if info_dict[info]['type'] == 'img':
                    self.SetCellRenderer(rnum, 0, ButtonRenderer('show'))
                    self.SetReadOnly(rnum, 0)
                    self.SetCellValue(rnum, 0, info_dict[info]['value'])  
                else:
                    self.SetCellValue(rnum, 0, info_dict[info]['value'])
            else:
                self.SetCellValue(rnum, 0, info_dict[info])
        self.AutoSize()
        self.GetGridWindow().Bind(wx.EVT_LEFT_DOWN, self.OnLeftClick)
    
    def OnLeftClick(self, event):
        x, y = self.CalcUnscrolledPosition(event.GetX(), event.GetY())
        coords = self.XYToCell(x, y)
        row = coords[0]
        col = coords[1]
        if isinstance(self.GetCellRenderer(row, col), ButtonRenderer):
            rect = self.GetCellRenderer(row, col).butt_rect
            if x >= rect.x and x <= rect.x+rect.width and \
                y>=rect.y and y<=rect.y+rect.height:
                ImageDialog(self.GetCellValue(row, col)).Show()
            else:
                event.Skip()
        else:
            event.Skip()
        
    def OnUpdate(self, info_dict):
        if self.GetNumberRows():
            self.DeleteRows(0, self.GetNumberRows())
        for info in info_dict:
            self.AppendRows(1)
            cnum = self.GetNumberRows() -1
            self.SetRowLabelValue(cnum, info)
            font = self.GetCellFont(cnum, 0)
            self.SetCellValue(cnum, 0, info_dict[info])
            self.SetReadOnly(cnum, 0)
        self.AutoSize()
        
class ButtonRenderer(wx.grid.PyGridCellRenderer):
    def __init__(self, label):
        wx.grid.PyGridCellRenderer.__init__(self)
        self.label = label
    
    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        rend = wx.RendererNative_GetDefault()
        dc.SetBrush(wx.Brush('white', wx.SOLID))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangleRect(rect)
        self.butt_rect = wx.Rect(rect.x+10, rect.y+5, 50, 30)
        rend.DrawPushButton(grid, dc, self.butt_rect, wx.ALIGN_CENTER)
        dc.DrawLabel(self.label, wx.Rect(rect.x+10, rect.y+5, 40, 30), wx.ALIGN_CENTER)
        
    def GetBestSize(self, grid, attr, dc, row, col):
        return wx.Size(70, 40)
    
    def Clone(self):
        return ButtonRenderer(self.label)

class ImageDialog(wx.Frame):
    def __init__(self, img_data):
        wx.Frame.__init__(self, None, -1)
        self.SetIcon(pe.getIcon())  
        img = PyEmbeddedImage(img_data)
        wx.StaticBitmap(self, -1, img.getBitmap())
        self.Fit()
        

class App(wx.App):
    def OnInit(self):
        mainframe = MainFrame()
        mainframe.CenterOnScreen()
        mainframe.Show()
        return True

if __name__ == "__main__":
    app = App(False)
    app.MainLoop()