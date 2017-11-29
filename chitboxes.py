import reportlab.pdfgen as pdfg
from reportlab.lib.pagesizes import LETTER, A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

import numpy as np
from numpy.linalg import norm
import PIL

import math


class ChitBoxGenerator:
    def __init__(self,
                 width,
                 height,
                 depth,
                 fname,
                 centreImage,
                 sideImage,
                 pagesize=LETTER):
        self.width = width
        self.height = height
        self.depth = depth
        self.centreImage = centreImage
        self.sideImage = sideImage
        self.pagesize = pagesize

        assert fname
        print 'generating to', fname, 'using', self.width, self.height, self.depth, self.centreImage, self.sideImage
        self.canvas = pdfg.canvas.Canvas(fname, pagesize=self.pagesize)
        self.filename = fname

    @staticmethod
    def fromRawData(raw_width,
                    raw_height,
                    raw_depth,
                    fname,
                    cIm,
                    sIm,
                    pagesize='letter'):
        cImRead = ImageReader(PIL.Image.open(cIm))
        sImRead = ImageReader(PIL.Image.open(sIm))
        ps = LETTER
        if pagesize == 'A4':
            ps = A4
        return ChitBoxGenerator(raw_width * cm, raw_height * cm,
                                raw_depth * cm, fname, cImRead, sImRead, ps)

    def drawCentre(self):
        self.canvas.drawImage(
            self.centreImage,
            -self.width / 2.0,
            -self.height / 2.0,
            self.width,
            self.height,
            preserveAspectRatio=False,
            mask='auto')

    def drawSide(self, width, height):
        self.canvas.drawImage(
            self.sideImage,
            -width / 2.0,
            -height / 2.0,
            width,
            height,
            preserveAspectRatio=False,
            mask='auto')

    def drawFullSides(self, offset, width, height):
        self.canvas.saveState()
        self.canvas.translate(0, offset + self.depth / 2.0)
        self.drawSide(width, height)
        self.canvas.translate(0, self.depth)
        self.canvas.rotate(180)
        self.drawSide(width, height)
        self.canvas.restoreState()

        self.canvas.saveState()
        self.canvas.translate(0, -offset - self.depth / 2.0)
        self.canvas.rotate(180)
        self.drawSide(width, height)
        self.canvas.rotate(180)
        self.canvas.translate(0, -self.depth)
        self.drawSide(width, height)
        self.canvas.restoreState()

    def drawRotatedSide(self, bottom, left):
        self.canvas.saveState()
        horizontalOffset = self.width / 2.0 + self.depth / 2.0
        if left:
            horizontalOffset = -horizontalOffset
        verticalOffset = self.height
        if bottom:
            verticalOffset = -verticalOffset
        self.canvas.translate(horizontalOffset, verticalOffset)
        angle = 90
        if left:
            angle = -angle
        self.canvas.rotate(angle)
        self.drawSide(self.height, self.depth)
        self.canvas.restoreState()

    def drawInnerBottom(self, direction):
        self.canvas.saveState()
        if direction in ('top', 'bottom'):
            offset = self.height
        else:
            offset = self.width
        offset += 2 * self.depth
        angle = 0
        if direction == 'right':
            angle = 90
        elif direction == 'bottom':
            angle = 180
        elif direction == 'left':
            angle = -90

        self.canvas.rotate(angle)
        self.canvas.translate(0, offset)
        self.canvas.rotate(angle)
        self.drawCentre()
        self.canvas.restoreState()

    def generatePage(self, scale=1.0):

        self.canvas.saveState()

        # everything's centred
        self.canvas.translate(self.pagesize[0] / 2.0, self.pagesize[1] / 2.0)
        self.canvas.scale(scale, scale)

        self.canvas.saveState()

        # most drawing is rotated 45 degrees
        # self.canvas.rotate(-45)

        self.drawCentre()

        # two sets of 4 sides in pairs to all sides of the centre
        self.drawFullSides(self.height / 2.0, self.width, self.depth)
        self.canvas.saveState()
        self.canvas.rotate(90)
        self.drawFullSides(self.width / 2.0, self.height, self.depth)
        self.canvas.restoreState()

        # the extra, cut-off sides
        self.drawRotatedSide(True, True)
        self.drawRotatedSide(True, False)
        self.drawRotatedSide(False, True)
        self.drawRotatedSide(False, False)

        self.drawInnerBottom('top')
        self.drawInnerBottom('left')
        self.drawInnerBottom('right')
        self.drawInnerBottom('bottom')

        c1 = (-self.width - 2 * self.depth, 0)
        c2 = (0, self.height + 2 * self.depth)
        c3 = (self.width + 2 * self.depth, 0)
        c4 = (0, -self.height - 2 * self.depth)
        #        for cs,ce in [(c1,c2),(c2,c3),(c3,c4),(c4,c1)]:
        #            self.canvas.line(cs[0],cs[1],ce[0],ce[1])

        for l in [(c1, c2), (c2, c3), (c3, c4), (c4, c1)]:
            v1 = np.array(l[0])
            v2 = np.array(l[1])
            v = v2 - v1
            self.canvas.saveState()
            self.canvas.translate(*l[0])
            self.canvas.rotate(math.degrees(math.atan2(v[1], v[0])))
            self.canvas.setFillColorCMYK(0.0, 0.0, 0.0, 0.0)
            self.canvas.line(0, 0, norm(v), 0)
            self.canvas.rect(-50 * cm, 0, 100 * cm, 50 * cm, fill=1, stroke=0)
            self.canvas.restoreState()
        self.canvas.restoreState()

        # we're now back to being centred on the page, but not rotated anymore
        # centreDiag = math.sqrt((self.width/2.0)**2+(self.height/2.0)**2)
        # diag = math.sqrt((2*self.depth)**2+self.width**2)
        # self.canvas.line(0,0,-math.sqrt(2.0)*self.height/2.0,0)
        # self.rect(
        self.canvas.restoreState()

    def generate(self):
        self.generatePage()
        self.canvas.showPage()
        self.generatePage(0.95)
        self.canvas.save()

    def generate_sample(self):
        import cStringIO
        from wand.image import Image
        buf = cStringIO.StringIO()
        tmp_fname = self.fname
        self.fname = buf
        self.generate()
        self.fname = tmp_fname
        sample_out = cStringIO.StringIO()
        with Image(blob=buf.getvalue(), resolution=75) as sample:
            sample.format = 'png'
            sample.save(sample_out)
            return sample_out


if __name__ == '__main__':
    c = ChitBoxGenerator(4.5 * cm, 4.5 * cm, 2.5 * cm, 'cob_ship.pdf',
                         'cob_ship.png', 'cob_ship_side.png')
    c.generate()
