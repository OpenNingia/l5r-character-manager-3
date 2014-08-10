# Copyright (C) 2011 Daniele Simonetti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import urllib2, os, sys, json, re
from PySide import QtCore, QtGui, QtNetwork

LAST_VERSION_URL = 'http://l5rcm.googlecode.com/svn/trunk/last_version'

def ver_cmp(version1, version2):
    def normalize(v):
        return [int(x) for x in re.sub(r'(\.0+)*$','', v).split(".")]
    return cmp(normalize(version1), normalize(version2))    

def get_last_version():
    try:
        request = urllib2.urlopen(LAST_VERSION_URL)
        response = request.read()	

    except urllib2.HTTPError, e:
        print 'Unable to get latest version info - HTTPError = ' + str(e.reason)
        return None

    except urllib2.URLError, e:
        print 'Unable to get latest version info - URLError = ' + str(e.reason)
        return None

    except Exception, e:
        import traceback
        print 'Unable to get latest version info - Exception = ' + traceback.format_exc()
        return None
        
    update_info = json.loads(response)
    return update_info
    
def need_update(my_version, last_version):
    return ver_cmp(last_version, my_version) > 0
    #return float(last_version) > float(my_version)
    
class DownloadManager(QtCore.QObject):
    def __init__(self, parent = None):
        super(DownloadManager, self).__init__(parent)
        
        self.manager = QtNetwork.QNetworkAccessManager()
        self.current_downloads = []
        self.download_dir = ''
        self.manager.finished.connect( self.on_download_finished )
        
    def set_download_dir(self, dir):
        self.download_dir = dir
        
    def do_download(self, url):
        q_url = QtCore.QUrl(url)
        request = QtNetwork.QNetworkRequest(q_url)
        reply = self.manager.get(request)        
        self.current_downloads.append(reply)
        return reply, self.save_file_name(q_url)
        
    def save_file_name(self, url):
        path = url.path()
        basename = os.path.basename(path)
        
        if basename == '':
            basename = 'download'
            
        basename = os.path.join(self.download_dir, basename)
            
        if os.path.exists(basename):
            # already exists, don't overwrite
            i = 0
            basename += '.'
            while os.path.exists( basename + str(i) ):
                i += 1
                
            basename += str(i)
        
        return basename
        
    def save_to_disk(self, filename, data):
        f = open(filename, 'w')
        if f is None:
            sys.stderr.write('Could not open %s for writing.\n' % filename)
            return False
        f.write( data.readAll() )
        f.close()
        return True
        
    def on_download_finished(self, reply):
        url = reply.url()
        if reply.error():
            sys.stderr.write('Download of %s failed: %s\n' % (url, reply.errorString()))
        else:
            filename = self.save_file_name(url)
            if self.save_to_disk(filename, reply):
                sys.stdout.write('Download of %s succeeded (saved to %s)\n' % (url, filename))
            
        self.current_downloads.remove(reply)
        reply.deleteLater()
  
class DownloadDialog(QtGui.QProgressDialog):
    def __init__(self, text, parent = None):
        super(DownloadDialog, self).__init__(text, 'Cancel', 0, 100, parent)        
        self.manager   = DownloadManager()
        self.handler   = None
        self.file_path = None

        self.canceled.connect( self.on_cancel )
                
    def exec_(self, destination, url):
        self.manager.set_download_dir(destination)
        self.handler, self.file_path = self.manager.do_download(url)
        self.handler.downloadProgress.connect(self.on_download_progress)
        #self.setLabelText('Downloading %s...' % url)
        
        return super(DownloadDialog, self).exec_()
        
    def on_download_progress(self, received, total):
        #print 'received %d of %d' % (received, total)
        progress = float(received) / float(total)
        #print 'progress = %f' % progress
        self.setValue( int( progress*100 ) )
        
    def on_cancel(self):
        if self.handler is not None:
            self.handler.abort()
            self.handler.close()
        
### MAIN ###
def main():
    app = QtGui.QApplication(sys.argv)

    update_info = get_last_version()
        
    dlg = DownloadDialog('Downloading...')
    dlg.setWindowTitle('Downloading last version...')
    print dlg.exec_('D:/Roba/Projects/l5rcm_rw/autoupdate', update_info['uri'])
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()