"""
This is a fully functional do nothing backend to provide a template to
backend writers.  It is fully functional in that you can select it as
a backend with

  import matplotlib
  matplotlib.use('Template')

and your matplotlib scripts will (should!) run without error, though
no output is produced.  This provides a nice starting point for
backend writers because you can selectively implement methods
(draw_rectangle, draw_lines, etc...) and slowly see your figure come
to life w/o having to have a full blown implementation before getting
any results.

Copy this to backend_xxx.py and replace all instances of 'template'
with 'xxx'.  Then implement the class methods and functions below, and
add 'xxx' to the switchyard in matplotlib/backends/__init__.py and
'xxx' to the backends list in the validate_backend methon in
matplotlib/__init__.py and you're off.  You can use your backend with::

  import matplotlib
  matplotlib.use('xxx')
  from pylab import *
  plot([1,2,3])
  show()

matplotlib also supports external backends, so you can place you can
use any module in your PYTHONPATH with the syntax::

  import matplotlib
  matplotlib.use('module://my_backend')

where my_backend.py is your module name.  This syntax is also
recognized in the rc file and in the -d argument in pylab, e.g.,::

  python simple_plot.py -dmodule://my_backend

If your backend implements support for saving figures (i.e. has a print_xyz()
method) you can register it as the default handler for a given file type

  from matplotlib.backend_bases import register_backend
  register_backend('xyz', 'my_backend', 'XYZ File Format')
  ...
  plt.savefig("figure.xyz")

The files that are most relevant to backend_writers are

  matplotlib/backends/backend_your_backend.py
  matplotlib/backend_bases.py
  matplotlib/backends/__init__.py
  matplotlib/__init__.py
  matplotlib/_pylab_helpers.py

Naming Conventions

  * classes Upper or MixedUpperCase

  * varables lower or lowerUpper

  * functions lower or underscore_separated

"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


import matplotlib
from matplotlib._pylab_helpers import Gcf
from matplotlib.backend_bases import RendererBase, GraphicsContextBase,\
     FigureManagerBase, FigureCanvasBase
from matplotlib.transforms import CompositeAffine2D
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox
import numpy as np

class RendererTemplate(RendererBase):
    """
    The renderer handles drawing/rendering operations.

    This is a minimal do-nothing class that can be used to get started when
    writing a new backend. Refer to backend_bases.RendererBase for
    documentation of the classes methods.
    """
    def __init__(self, width, height, dpi):
        self.width = width
        self.height = height
        self.dw = dpi*width
        self.dh = dpi*height
        arr = [" "]*self.dw
        self.arr = [arr[:] for i in xrange(0, self.dh)]
        self.colors = {}
        self.dpi = dpi

    def __draw_point(self, p, color="rgb(0,0,0)"):
        from math import floor
        x = int(floor(p[0]))
        y = int(floor(p[1]))
        if x<0 or x>=self.dw or y<0 or y>=self.dh:
            return
        self.arr[y][x] = '*'
        self.colors[(x, y)] = color

    def __draw_line(self, p1, p2, color="rgb(0,0,0)"):
        v = p2 - p1
        l = np.linalg.norm(v)
        dr = v/l
        r = np.zeros(v.shape[0])
        while np.linalg.norm(r) < l:
            self.__draw_point(p1+r, color)
            r = r+dr

    def __draw_bezier3(self, p1, p2, p3, N=100, color="rgb(0,0,0)"):
        dt = 1./N
        t = 0.
        p = p1
        while t <= 1.:
            t += dt
            p4 = p1 + (p2 - p1)*t
            p5 = p2 + (p3 - p2)*t
            n  = p4 + (p5 - p4)*t
            self.__draw_line(p, n, color)
            p = n

    def __draw_bezier4(self, p1, p2, p3, p4, N=100, color="rgb(0,0,0)"):
        dt = 1./N
        t = 0.
        p = p1
        while t <= 1.:
            t += dt
            p5 = p1 + (p2 - p1)*t
            p6 = p2 + (p3 - p2)*t
            p7 = p3 + (p4 - p3)*t
            p8 = p5 + (p6 - p5)*t
            p9 = p6 + (p7 - p6)*t
            n  = p8 + (p9 - p8)*t
            self.__draw_line(p, n, color)
            p = n

    def draw_path(self, gc, path, transform, rgbFace=None):
        def to_code(color):
            return "rgb(" + ",".join([str(int(255*color[i])) for i in range(0, 3)]) + ")"

        mat = transform.get_matrix()
        c = to_code(gc.get_rgb())
        
        def apply_affine(p):
            p = np.array(list(p) + [1])
            return mat.dot(p)
        
        cp = np.zeros(4, dtype=np.float32)
        arr = []
        
        if path.codes is None:
            l = len(path.vertices)
            for i2 in range(1, l):
                p1 = apply_affine(path.vertices[i2-1])
                p2 = apply_affine(path.vertices[i2])
                self.__draw_line(p1, p2, color=c)
        else:
            for i, code in enumerate(path.codes):
                p = apply_affine(path.vertices[i])
                
                if   code == 1:
                    # moveto
                    cp = p
                elif code == 2:
                    # lineto
                    self.__draw_line(cp, p, color=c)
                    cp = p
                elif code == 3:
                    # curve3
                    arr.append(p)
                    if len(arr) == 2:
                        self.__draw_bezier3(cp, arr[0], arr[1], color=c)
                        arr = []
                        cp = p
                        
                elif code == 4:
                    # curve4
                    arr.append(p)
                    if len(arr)==3:
                        self.__draw_bezier4(cp, arr[0], arr[1], arr[2], color=c)
                        arr = []
                        cp = p
                    
                elif code == 79:
                    arr = []
                else:
                    raise Exception("parse error")
            pass

    # draw_markers is optional, and we get more correct relative
    # timings by leaving it out.  backend implementers concerned with
    # performance will probably want to implement it
#     def draw_markers(self, gc, marker_path, marker_trans, path, trans, rgbFace=None):
#         pass

    # draw_path_collection is optional, and we get more correct
    # relative timings by leaving it out. backend implementers concerned with
    # performance will probably want to implement it
#     def draw_path_collection(self, gc, master_transform, paths,
#                              all_transforms, offsets, offsetTrans, facecolors,
#                              edgecolors, linewidths, linestyles,
#                              antialiaseds):
#         pass

    # draw_quad_mesh is optional, and we get more correct
    # relative timings by leaving it out.  backend implementers concerned with
    # performance will probably want to implement it
#     def draw_quad_mesh(self, gc, master_transform, meshWidth, meshHeight,
#                        coordinates, offsets, offsetTrans, facecolors,
#                        antialiased, edgecolors):
#         pass

    def draw_image(self, gc, x, y, im):
        pass

    def draw_text(self, gc, x, y, s, prop, angle, ismath=False, mtext=None):
        from math import floor
        x_ = int(floor(x))
        y_ = int(floor(y))
        for i, c in enumerate(s):
            nx = x_ + i
            if x<0 or x>=self.dw or y<0 or y>=self.dh:
                return
            self.arr[y_][nx] = c

    def flipy(self):
        return True

    def get_canvas_width_height(self):
        return self.dw, self.dh

    def get_text_width_height_descent(self, s, prop, ismath):
        return 1, 1, 1

    def new_gc(self):
        return GraphicsContextBase()

    def points_to_pixels(self, points):
        # if backend doesn't have dpi, e.g., postscript or svg
        return points
        # elif backend assumes a value for pixels_per_inch
        #return points/72.0 * self.dpi.get() * pixels_per_inch/72.0
        # else
        #return points/72.0 * self.dpi.get()


class GraphicsContextTemplate(GraphicsContextBase):
    """
    The graphics context provides the color, line styles, etc...  See the gtk
    and postscript backends for examples of mapping the graphics context
    attributes (cap styles, join styles, line widths, colors) to a particular
    backend.  In GTK this is done by wrapping a gtk.gdk.GC object and
    forwarding the appropriate calls to it using a dictionary mapping styles
    to gdk constants.  In Postscript, all the work is done by the renderer,
    mapping line styles to postscript calls.

    If it's more appropriate to do the mapping at the renderer level (as in
    the postscript backend), you don't need to override any of the GC methods.
    If it's more appropriate to wrap an instance (as in the GTK backend) and
    do the mapping here, you'll need to override several of the setter
    methods.

    The base GraphicsContext stores colors as a RGB tuple on the unit
    interval, e.g., (0.5, 0.0, 1.0). You may need to map this to colors
    appropriate for your backend.
    """
    pass



########################################################################
#
# The following functions and classes are for pylab and implement
# window/figure managers, etc...
#
########################################################################

def draw_if_interactive():
    """
    For image backends - is not required
    For GUI backends - this should be overriden if drawing should be done in
    interactive python mode
    """
    pass

def show():
    from IPython.core.display import display, HTML
    """
    For image backends - is not required
    For GUI backends - show() is usually the last line of a pylab script and
    tells the backend that it is time to draw.  In interactive mode, this may
    be a do nothing func.  See the GTK backend for an example of how to handle
    interactive versus batch mode
    """
    try:
        for manager in Gcf.get_all_fig_managers():
            canvas = manager.canvas
            canvas.draw()
            colors = canvas.colors
            
            string = canvas.to_str("<br>", color=True)
            display(HTML("<div style=\"font-size:2px; line-height:90%;\"><tt>" + string + "</tt></div>"))
    finally:
        #if close and Gcf.get_all_fig_managers():
        #    matplotlib.pyplot.close('all')
        pass

def new_figure_manager(num, *args, **kwargs):
    """
    Create a new figure manager instance
    """
    # if a main-level app must be created, this (and
    # new_figure_manager_given_figure) is the usual place to
    # do it -- see backend_wx, backend_wxagg and backend_tkagg for
    # examples.  Not all GUIs require explicit instantiation of a
    # main-level app (egg backend_gtk, backend_gtkagg) for pylab
    FigureClass = kwargs.pop('FigureClass', Figure)
    thisFig = FigureClass(*args, **kwargs)
    return new_figure_manager_given_figure(num, thisFig)

def new_figure_manager_given_figure(num, figure):
    """
    Create a new figure manager instance for the given figure.
    """
    canvas = FigureCanvasTemplate(figure)
    manager = FigureManagerTemplate(canvas, num)
    return manager

class FigureCanvasTemplate(FigureCanvasBase):
    """
    The canvas the figure renders into.  Calls the draw and print fig
    methods, creates the renderers, etc...

    Public attribute

      figure - A Figure instance

    Note GUI templates will want to connect events for button presses,
    mouse movements and key presses to functions that call the base
    class methods button_press_event, button_release_event,
    motion_notify_event, key_press_event, and key_release_event.  See,
    e.g., backend_gtk.py, backend_wx.py and backend_tkagg.py
    """

    def draw(self):
        """
        Draw the figure using the renderer
        """
        from math import ceil
        width, height = 9., 3.
        self.figure.set_size_inches(width, height)
        self.dpi = 15
        self.figure.set_dpi(self.dpi)
        renderer = RendererTemplate(int(ceil(width)), int(ceil(height)), self.dpi)
        self.figure.draw(renderer)
        self.arr = renderer.arr
        self.colors = renderer.colors

    def to_str(self, sep="\n", color=None):
        arrs = [['&nbsp;' if c==" " else c for c in arr] for arr in self.arr]
        
        if color is not None:
            for xy, c in self.colors.items():
                x, y = xy
                arrs[y][x] = "<span style=\"color:" + c + "\">" + arrs[y][x] + "</span>"
        
        return sep.join(["".join(arr) for arr in arrs])

    # You should provide a print_xxx function for every file format
    # you can write.

    # If the file type is not in the base set of filetypes,
    # you should add it to the class-scope filetypes dictionary as follows:
    # filetypes = FigureCanvasBase.filetypes.copy()
    filetypes = {}
    filetypes['txt'] = 'Text format'

    def print_txt(self, filename, *args, **kwargs):
        """
        Write out format foo.  The dpi, facecolor and edgecolor are restored
        to their original values after this call, so you don't need to
        save and restore them.
        """
        self.draw()
        f = open(filename, 'w')
        f.write(self.to_str())
        f.close()

    def get_default_filetype(self):
        return 'txt'

class FigureManagerTemplate(FigureManagerBase):
    """
    Wrap everything up into a window for the pylab interface

    For non interactive backends, the base class does all the work
    """
    pass

########################################################################
#
# Now just provide the standard names that backend.__init__ is expecting
#
########################################################################

FigureCanvas = FigureCanvasTemplate
FigureManager = FigureManagerTemplate
