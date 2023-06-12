#!/usr/bin/env python
# coding=utf-8
#
# Copyright (C) [YEAR] [YOUR NAME], [YOUR EMAIL]
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
"""
Description of this extension
"""
import sys

import inkex

class XPlaneProfileMarkSection(inkex.EffectExtension):
    construction_layer: inkex.Layer

    def add_arguments(self, pars):
        pars.add_argument("--first_section_index", type=int, \
                          help="The index to generate for the first selected section, incremented for remainder")

    def effect(self):
        for elem in self.svg.selection:
            # selected elements should be paths!
            if not isinstance(elem, inkex.PathElement) and not isinstance(elem, inkex.ShapeElement):
                inkex.utils.errormsg("selection should contain only individual paths or shapes! The selected element with eid: {} is a {} skipping".format(elem.eid, elem.typename))
                break

            #add the center tag
            elem.set("{uri://x-plane}profile-path", "true")


# standalone test command line paramenters: test\drawing.svg --output=test\drawing-out.svg --id=path249 --id=path287 --id=rect341 --id=path427
if __name__ == '__main__':
    #inkex.utils.errormsg("Args: {}".format(sys.argv))
    XPlaneProfileMarkSection().run()
