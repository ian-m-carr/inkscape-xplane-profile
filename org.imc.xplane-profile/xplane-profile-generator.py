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
from typing import List, Tuple

import io
import pathlib
import inkex
from inkex.transforms import Vector2d, Transform
from inkex.utils import errormsg
from construction_layer_mgr import find_construction_layer, find_sections_in_group

# conversion factor from meters to feet (ACF file is in ft!)
CONV_M_TO_FT = 3.28084

'''
def draw_points_along_bezier_curve():
    retval = []
    style1 = {'fill': 'none', 'stroke': 'green', 'stroke-width': '.1'}
    style2 = {'fill': 'none', 'stroke': 'red', 'stroke-width': '.1'}
    self.construction_layer.append(inkex.Circle.new(center=current_pos, radius=1, style=style1))
    self.construction_layer.append(inkex.Circle.new(center=points[0], radius=1, style=style2))
    self.construction_layer.append(inkex.Circle.new(center=points[1], radius=1, style=style2))
    self.construction_layer.append(inkex.Circle.new(center=points[2], radius=1, style=style1))


    for i in range(1,10):
        retval.append(inkex.bezier.bezierpointatt(bez, i/10))
'''


class XPlaneProfileGenerator(inkex.EffectExtension):
    construction_layer: inkex.Layer

    """Please rename this class, don't keep it unnamed"""

    def add_arguments(self, pars):
        pars.add_argument("--scale-factor", type=float, help="Scale factor")
        pars.add_argument("--num-radii-per-side", type=int, help="The number of sample points to take per side")
        pars.add_argument("--acf-output-file", type=str, help="The number of sample points to take per side")

    def effect(self):
        # inkex.utils.errormsg("File:" + inkex.__file__)
        # inkex.utils.errormsg("Exe:" + sys.executable)
        # inkex.utils.errormsg("Path:" + str(sys.path))

        # look for an existing construction layer or create a new one!
        self.construction_layer = find_construction_layer(self.svg)

        style = {'fill': 'none', 'stroke': 'blue', 'stroke-width': '.1'}

        # deal with the output file
        o_file = None
        if self.options.acf_output_file:
            of_path = pathlib.Path(self.options.acf_output_file)
            if of_path.is_file():
                backup_path = of_path.with_suffix(of_path.suffix + '.bak')
                if backup_path.exists():
                    backup_path.unlink()
                of_path.rename(backup_path)

            o_file = of_path.open('w')

        try:
            for elem in self.svg.selection:
                # selected element should be a group!
                if not isinstance(elem, inkex.Group):
                    errormsg("selection should contain only groups! The selected element with eid: {} is a {} skipping".format(elem.eid, elem.typename))
                    break

                # the group should be marked up as an x-plane:section or contain descendants marked up as such
                sections = find_sections_in_group(self.svg, elem)

                if len(sections) == 0:
                    errormsg(
                        "The selected element with eid: {} is not marked as an x-plane section, nor does it contain any".format(elem.eid, elem.typename))
                    break

                # iterate through each section element
                indx = 0
                for section in sections:
                    (valid, section_indx, section_z, profile_el, center_el) = section

                    if not valid:
                        errormsg(
                            "The selected element, with eid: {}, is not a validly marked up section check the index, z, center and profile markup!".format(
                                elem.eid))
                        break

                    # find the path element
                    parent = self.construction_layer

                    # derive the profile and center transforms
                    pel_trans: Transform = profile_el.composed_transform()
                    cen_trans: Transform = center_el.composed_transform()

                    # center of the bounding box
                    center_point = inkex.Path(center_el.get_path()).bounding_box().center
                    # absolute position by applying all transforms
                    center_point = cen_trans.apply_to_point(center_point)

                    pth = inkex.Path(profile_el.get_path()).transform(pel_trans)
                    path_box = pth.bounding_box()

                    current_group = inkex.Group.new(label='element_construction_{}'.format(elem.eid))
                    current_group.transform = elem.composed_transform()
                    parent.append(current_group)

                    # mark the center of the bounding box
                    current_group.append(inkex.Circle.new(center=path_box.center, radius=1))

                    # set up the initial coordinates for our intersection fan
                    start = path_box.center
                    end = path_box.center + Vector2d(0, -max(path_box.width, path_box.height))

                    points = []

                    # the number of radii samples per side
                    num_radii_per_side = self.options.num_radii_per_side

                    # fan from the bounding box center at 10 degree increments 0-180
                    step = 180 / (num_radii_per_side - 1)
                    for i in range(0, num_radii_per_side):
                        ang = step * i
                        # rotate the end coord around the box center
                        tx = Transform().add_rotate(ang, path_box.center)
                        end1 = tx.apply_to_point(end)

                        # add a construction line to the diagram
                        lin = inkex.Line.new(start=start, end=end1, style=style)
                        current_group.append(lin)

                        # look for intersections between the line and the path
                        intersections = self.iterate_path_and_intersect_line(pth, lin)

                        for intersection in intersections:
                            points.append(intersection)

                    # output the acf file content
                    if o_file:
                        self.write_station_elements(o_file, section_indx, section_z, center_point, points)

                    # draw a circle at each intersection point
                    for point in points:
                        circ = inkex.Circle.new(center=point, radius=1, style=style)
                        circ.transform = elem.transform
                        current_group.append(circ)
        finally:
            if o_file:
                o_file.close()
    def iterate_path_and_intersect_line(self, pth: inkex.Path, lin: inkex.Line) -> List[Tuple[float, float]]:
        retval = []

        # intialize to 0,0
        current_pos = inkex.Vector2d(0, 0)

        # convert to a superpath and convert all the segments to curves
        for segment in pth.to_superpath().to_segments(True):
            if segment.name == 'Move':
                # just update the current drawing position
                current_pos = inkex.Vector2d(segment.x, segment.y)
            else:
                intersections = self.intersect_line_and_curve(((lin.x1, lin.y1), (lin.x2, lin.y2)), current_pos, segment)

                if intersections:
                    for intersection in intersections:
                        retval.append(intersection)

                # move to the end of the curve section
                current_pos = inkex.Vector2d(segment.x4, segment.y4)

        return retval

    def intersect_line_and_curve(self, lin: inkex.Line, at_pos: inkex.Vector2d, curve: inkex.paths.Curve) -> List[Tuple[float, float]]:
        ((lx1, ly1), (lx2, ly2)) = lin
        points = curve.to_bez()
        bez = (at_pos, points[0], points[1], points[2])

        intersections = inkex.bezier.linebezierintersect(lin, bez)

        retval = []

        # we only want the intersections on the line segment passed in!
        # by default, we get all the intersections for the projected infinite length line, forward and backward!
        for intersection in intersections:
            (ix1, ix2) = intersection
            # deal with the rounding errors
            if inkex.paths.CubicSuperPath.is_on([round(ix1, 4), round(ix2, 4)], [round(lx1, 4), round(ly1, 4)], [round(lx2, 4), round(ly2, 4)], 1e-2):
                retval.append(intersection)

        return retval

    def write_station_elements(self, o_file: io.TextIOBase, station_indx: int, station_z: float, station_center: inkex.Vector2d, points: List[inkex.Vector2d]):
        # points are reflected in X so for 8 intersections we have 16 points 0-15
        num_points = len(points) * 2

        for point_indx in range(len(points)):
            # position 0 -> (n/2-1)
            self.write_station_element(o_file, station_indx, station_z, point_indx,
                                       points[point_indx][0] - station_center.x,
                                       points[point_indx][1] - station_center.y)
            # reflected in x (n-1) -> n/2
            self.write_station_element(o_file, station_indx, station_z, num_points - 1 - point_indx,
                                       -(points[point_indx][0] - station_center.x),
                                       points[point_indx][1] - station_center.y)

    def write_station_element(self, o_file: io.TextIOBase, station_indx: int, station_z: float, point_indx: int, x: float, y: float):
        body_num = 0
        # X scaled by file scaling and converted m->ft
        x = x * float(self.options.scale_factor) * CONV_M_TO_FT
        print('P _body/{}/_geo_xyz/{},{},0 {}'.format(body_num, station_indx, point_indx, round(x, 4)), file=o_file)
        # Y
        y = y * float(self.options.scale_factor) * CONV_M_TO_FT
        print('P _body/{}/_geo_xyz/{},{},1 {}'.format(body_num, station_indx, point_indx, round(y, 4)), file=o_file)
        # Z
        print('P _body/{}/_geo_xyz/{},{},2 {}'.format(body_num, station_indx, point_indx, round(station_z, 4)), file=o_file)


# standalone test command line paramenters: test\drawing.svg --output=test\drawing-out.svg --id=path249 --id=path287 --id=rect341 --id=path427
if __name__ == '__main__':
    XPlaneProfileGenerator().run()
