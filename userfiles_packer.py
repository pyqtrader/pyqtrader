#Converter of user files and directories to userfiles.py
import os,cfg
import userfiles as uf
from _debugger import (_p,_pc,_c,_callers,_exinfo,_printcallers,_ptime,_print)

def pack(): #packs userfiles from the user directories, used in production only
    filetree=[]#[dict(root=cfg.MAIN_DIR,files={'__init__.py':''})]
    with open(f'{cfg.MAIN_DIR}LICENSE','r') as f:
        lcontent=dict(LICENSE=f.read())
    filetree.append(dict(root=cfg.MAIN_DIR,files=lcontent))
    for uadir in cfg.USER_DIRECTORIES:
        for root, dirs, files in os.walk(uadir):
            contents={}
            if '__pycache__' not in root:
                for fl in files:
                    if fl in cfg.USERFILESLIST:
                        with open(f'{root}/{fl}','r') as f:
                            contents[fl]=f.read()
                        if fl==cfg.ACCT_FILE:
                            contents[fl]=cfg.ACCT_DETAILS
                    if root==cfg.ASSETS_DIR:
                        with open(f'{root}/{fl}','rb') as f:
                            contents[fl]=f.read().decode('latin-1')
                filetree.append(dict(root=root,files=contents))
        ft='filetree='+str(filetree)
        with open('userfiles.py','w') as f:
            f.write(f'{ft}\n')

def unpack(): #unpacks userfiles to the user directories
    for el in uf.filetree:
        os.makedirs(el['root'],exist_ok=True)
        for file in el['files']:
            filepath=f'{el["root"]}/{file}'
            if not os.path.isfile(filepath):
                if '.py' in file:
                    with open(filepath,'w') as f:
                        f.write(el['files'][file])
                if '.png' in file:
                    with open(filepath,'wb') as f:
                        f.write(el['files'][file].encode('latin-1'))
                if 'LICENSE'==file:
                    with open(filepath,'w') as f:
                        f.write(el['files'][file])

if __name__=='__main__':
    pack()