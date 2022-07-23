import codecs
import bitstring
from PIL import Image
from pathlib import Path
import argparse
import csv
import re
import jaconv

class CO59_to_utf8:
    def __init__(self, euc_co59_file='euc_co59.dat'):
        with codecs.open(euc_co59_file, 'r', 'euc-jp') as f:
            co59t = f.read()
        co59l = co59t.split()
        self.conv = {}
        for c in co59l:
            ch = c.split(':')
            co = ch[1].split(',')
            co59c = (int(co[0]), int(co[1]))
            self.conv[co59c] = ch[0]

    def __call__(self, co59):
        return self.conv[co59]

def T56(c):
    t56s = '0123456789[#@:>? ABCDEFGHI&.](<  JKLMNOPQR-$*);\'|/STUVWXYZ ,%="!'
    return t56s[c]

class ETLn_Record:
    def read(self, bs, pos=None):
        if pos:
            f.bytepos = pos * self.octets_per_record

        r = bs.readlist(self.bitstring)

        record = dict(zip(self.fields, r))

        self.record = {
            k: (self.converter[k](v) if k in self.converter else v)
            for k, v in record.items()
        }

        return self.record

    def get_image(self):
        return self.record['Image Data']

class ETL167_Record(ETLn_Record):
    def __init__(self):
        self.octets_per_record = 2052
        self.fields = [
            "Data Number", "Character Code", "Serial Sheet Number", "JIS Code", "EBCDIC Code",
            "Evaluation of Individual Character Image", "Evaluation of Character Group",
            "Male-Female Code", "Age of Writer", "Serial Data Number",
            "Industry Classification Code", "Occupation Classification Code",
            "Sheet Gatherring Date", "Scanning Date",
            "Sample Position Y on Sheet", "Sample Position X on Sheet",
            "Minimum Scanned Level", "Maximum Scanned Level", "Image Data"
        ]
        self.bitstring = 'uint:16,bytes:2,uint:16,hex:8,hex:8,4*uint:8,uint:32,4*uint:16,4*uint:8,pad:32,bytes:2016,pad:32'
        self.converter = {
            'Character Code': lambda x: x.decode('ascii'),
            'Image Data': lambda x: Image.eval(Image.frombytes('F', (64, 63), x, 'bit', 4).convert('L'),
                                               lambda x: x * 16)
        }

    def get_char(self):
        return bytes.fromhex(self.record['JIS Code']).decode('iso2022_jp')

class ETL2_Record(ETLn_Record):
    def __init__(self):
        self.octets_per_record = 2745
        self.fields = [
            "Serial Data Number", "Mark of Style", "Contents", "Style", "CO-59 Code", "Image Data"
        ]
        self.bitstring = 'uint:36,uint:6,pad:30,bits:36,bits:36,pad:24,bits:12,pad:180,bytes:2700'
        self.converter = {
            'Mark of Style': lambda x: T56(x),
            'Contents': lambda x: ''.join([T56(b.uint) for b in x.cut(6)]),
            'CO-59 Code': lambda x: tuple([b.uint for b in x.cut(6)]),
            'Style': lambda x: ''.join([T56(b.uint) for b in x.cut(6)]),
            'Image Data': lambda x: Image.eval(Image.frombytes('F', (60, 60), x, 'bit', 6).convert('L'),
                                               lambda x: x * 4)
        }
        self.co59_to_utf8 = co59_to_utf8 = CO59_to_utf8(
            'euc_co59.dat')

    def get_char(self):
        return self.co59_to_utf8(self.record['CO-59 Code'])

class ETL345_Record(ETLn_Record):
    def __init__(self):
        self.octets_per_record = 2952
        self.fields = [
            "Serial Data Number", "Serial Sheet Number", "JIS Code", "EBCDIC Code", "4 Character Code",
            "Evaluation of Individual Character Image", "Evaluation of Character Group",
            "Sample Position Y on Sheet", "Sample Position X on Sheet",
            "Male-Female Code", "Age of Writer", "Industry Classification Code", "Occupation Classification Code",
            "Sheet Gatherring Date", "Scanning Date", "Number of X-Axis Sampling Points",
            "Number of Y-Axis Sampling Points", "Number of Levels of Pixel",
            "Magnification of Scanning Lenz", "Serial Data Number (old)", "Image Data"        
        ]
        self.bitstring = 'uint:36,uint:36,hex:8,pad:28,hex:8,pad:28,bits:24,pad:12,15*uint:36,pad:1008,bytes:2736'
        self.converter = {
            '4 Character Code': lambda x: ''.join([ T56(b.uint) for b in x.cut(6) ]),
            'Image Data': lambda x: Image.eval(Image.frombytes('F', (72,76), x, 'bit', 4).convert('L'),
            lambda x: x * 16)
        }

    def get_char(self):
        
        char = bytes.fromhex(self.record['JIS Code']).decode('shift_jis')
        if self.record['4 Character Code'][0] == 'H':
            char = jaconv.kata2hira(jaconv.han2zen(char)).replace(
                'ぃ', 'ゐ').replace('ぇ', 'ゑ')
        elif self.record['4 Character Code'][0] == 'K':
            char = jaconv.han2zen(char).replace('ィ', 'ヰ').replace('ェ', 'ヱ')

        return char
        
class ETL8G_Record(ETLn_Record):
    def __init__(self):
        self.octets_per_record = 8199
        self.fields = [
            "Serial Sheet Number", "JIS Kanji Code", "JIS Typical Reading", "Serial Data Number",
            "Evaluation of Individual Character Image", "Evaluation of Character Group",
            "Male-Female Code", "Age of Writer",
            "Industry Classification Code", "Occupation Classification Code",
            "Sheet Gatherring Date", "Scanning Date",
            "Sample Position X on Sheet", "Sample Position Y on Sheet", "Image Data"
        ]
        self.bitstring = 'uint:16,hex:16,bytes:8,uint:32,4*uint:8,4*uint:16,2*uint:8,pad:240,bytes:8128,pad:88'
        self.converter = {
            'JIS Typical Reading': lambda x: x.decode('ascii'),
            'Image Data': lambda x: Image.eval(Image.frombytes('F', (128, 127), x, 'bit', 4).convert('L'),
            lambda x: x * 16)
        }
    
    def get_char(self):
        char = bytes.fromhex(
            '1b2442' + self.record['JIS Kanji Code'] + '1b2842').decode('iso2022_jp')
        return char

class ETL8B_Record(ETLn_Record):
    def __init__(self):
        self.octets_per_record = 512
        self.fields = [
            "Serial Sheet Number", "JIS Kanji Code", "JIS Typical Reading", "Image Data"
        ]
        self.bitstring = 'uint:16,hex:16,bytes:4,bytes:504'
        self.converter = {
            'JIS Typical Reading': lambda x: x.decode('ascii'),
            'Image Data': lambda x: Image.frombytes('1', (64, 63), x, 'raw')
        }

    def get_char(self):
        char = bytes.fromhex(
            '1b2442' + self.record['JIS Kanji Code'] + '1b2842').decode('iso2022_jp')
        return char

class ETL9G_Record(ETLn_Record):
    def __init__(self):
        self.octets_per_record = 8199
        self.fields = [
            "Serial Sheet Number", "JIS Kanji Code", "JIS Typical Reading", "Serial Data Number",
            "Evaluation of Individual Character Image", "Evaluation of Character Group",
            "Male-Female Code", "Age of Writer",
            "Industry Classification Code", "Occupation Classification Code",
            "Sheet Gatherring Date", "Scanning Date",
            "Sample Position X on Sheet", "Sample Position Y on Sheet", "Image Data"
        ]
        self.bitstring = 'uint:16,hex:16,bytes:8,uint:32,4*uint:8,4*uint:16,2*uint:8,pad:272,bytes:8128,pad:56'
        self.converter = {
            'JIS Typical Reading': lambda x: x.decode('ascii'),
            'Image Data': lambda x: Image.eval(Image.frombytes('F', (128, 127), x, 'bit', 4).convert('L'),
                                               lambda x: x * 16)
        }

    def get_char(self):
        char = bytes.fromhex(
            '1b2442' + self.record['JIS Kanji Code'] + '1b2842').decode('iso2022_jp')
        return char

class ETL9B_Record(ETLn_Record):
    def __init__(self):
        self.octets_per_record = 576
        self.fields = [
            "Serial Sheet Number", "JIS Kanji Code", "JIS Typical Reading", "Image Data"
        ]
        self.bitstring = 'uint:16,hex:16,bytes:4,bytes:504,pad:512'
        self.converter = {
            'JIS Typical Reading': lambda x: x.decode('ascii'),
            'Image Data': lambda x: Image.frombytes('1', (64, 63), x, 'raw')
        }
        
    def get_char(self):
        char = bytes.fromhex(
            '1b2442' + self.record['JIS Kanji Code'] + '1b2842').decode('iso2022_jp')
        return char

def unpack(filename, etln_record):

    base = Path(filename).name
    folder = Path(filename).parent

    f = bitstring.ConstBitStream(filename=filename)

    if re.match(r'ETL[89]B_Record', etln_record.__class__.__name__):
        f.bytepos = etln_record.octets_per_record

    chars = []
    images = []
    records = []

    rows, cols = 40, 50
    rows_by_cols = rows * cols

    c = 0

    while f.pos < f.length:

        record = etln_record.read(f)
        char = etln_record.get_char()
        img = etln_record.get_image()

        chars.append(char)
        images.append(img)
        records.append(record)

        if len(chars) % rows_by_cols == 0 or f.pos >= f.length:

            txt = '\n'.join([''.join(chars[j * cols: (j + 1) * cols])
                             for j in range(rows)])
            txtfn = folder / '{}_{:02d}.txt'.format(base, c)
            
            with open(txtfn, 'w') as txtf:
                txtf.write(txt)

            w, h = images[0].width, images[0].height

            tiled = Image.new(images[0].mode, (w * cols, h * rows))

            for ij in range(len(images)):
                i, j = ij % cols, ij // cols
                tiled.paste(images[ij], (w * i, h * j))

            tiledfn = folder / '{}_{:02d}.png'.format(base, c)
            tiled.save(tiledfn)

            chars = []
            images = []
            c += 1

    csvfn = folder / '{}.csv'.format(base)

    with open(csvfn, 'w') as rf:
        writer = csv.writer(rf)
        writer.writerow(etln_record.fields[:-1])
        for ir in records:
            writer.writerow(list(ir.values())[:-1])

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Decompose ETLn files')
    parser.add_argument('input', help='input files')

    args = parser.parse_args()

    base = Path(args.input).name

    if re.match(r'ETL[167]', base):
        etln_record = ETL167_Record()
    elif re.match(r'ETL2', base):
        etln_record = ETL2_Record()
    elif re.match(r'ETL[345]', base):
        etln_record = ETL345_Record()
    elif re.match(r'ETL8G', base):
        etln_record = ETL8G_Record()
    elif re.match(r'ETL8B', base):
        etln_record = ETL8B_Record()
    elif re.match(r'ETL9G', base):
        etln_record = ETL9G_Record()
    elif re.match(r'ETL9B', base):
        etln_record = ETL9B_Record()

    unpack(args.input, etln_record)
