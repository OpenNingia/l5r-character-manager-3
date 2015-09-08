import exporters
import models

import dal
import os


class NpcExportTest(object):

    def __init__(self):

        self.out = 'npc.fdf'
        self.inp = [
            'pc1.l5r',
            'pc2.l5r'
        ]

        pcs = []

        for f in self.inp:
            c = models.AdvancedPcModel()
            if c.load_from(f):
                pcs.append(c)

        user_data_dir = os.environ['APPDATA'].decode('latin-1')
        pack_data_dir = os.path.join(user_data_dir, 'openningia', 'l5rcm')

        dstore = dal.Data(
            [os.path.join(pack_data_dir, 'core.data'),
             os.path.join(pack_data_dir, 'data')],
            [])

        exporter = exporters.FDFExporterTwoNPC(pcs)

        with open(self.out, 'wb') as fobj:
            exporter.export(fobj)

if __name__ == '__main__':

    n = NpcExportTest()
