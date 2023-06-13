from typing import List, Tuple

import inkex
from inkex import utils, Group, Layer, Rectangle, TextElement, Tspan, SvgDocumentElement

NSMAP = {
    'svg': 'http://www.w3.org/2000/svg',
    'inkscape': 'http://www.inkscape.org/namespaces/inkscape',
    'xplane': 'uri://x-plane'
}


def find_sections_in_group(svg: SvgDocumentElement, grp: Group, update_info: bool = False, layer: Layer = None) -> List[
    Tuple[bool, int, float, inkex.BaseElement, inkex.BaseElement]]:
    # check the group and it's descendants extracting any that are marked up as sections
    xpth = "descendant-or-self::svg:g[@xplane:profile-section]"
    section_els = grp.xpath(xpth, NSMAP)

    valid_sections = []
    for section_el in section_els:
        tuple = validate_section_structure(svg, section_el, update_info, layer)
        if tuple[0]:
            valid_sections.append(tuple)

    return valid_sections


def validate_section_structure(svg: SvgDocumentElement, grp: Group, update_info: bool = False, layer: Layer = None) -> Tuple[
    bool, int, float, inkex.BaseElement, inkex.BaseElement]:
    good = True

    # group should have
    # "{uri://x-plane}profile-section" true
    is_section = grp.get("{uri://x-plane}profile-section", False)
    if is_section != "true":
        utils.errormsg("Expected group {} to carry the profile-section attribute with a value 'true'".format(grp.eid))
        good = False

    # "{uri://x-plane}profile-section-index" an integer value
    section_index = int(grp.get("{uri://x-plane}profile-section-index", 0))
    # "{uri://x-plane}profile-section_z" a float value
    section_z = float(grp.get("{uri://x-plane}profile-section_z", 0.0))

    # a child path or shape carrying the "{uri://x-plane}profile-center" marker value true
    xpth = ".//svg:*[@xplane:profile-center]"
    center_els = grp.xpath(xpth, NSMAP)

    center_id = '[none]'
    if len(center_els) == 0:
        utils.errormsg("Expected group {} to contain a path/shape marked as the center".format(grp.eid))
        good = False
    elif len(center_els) > 1:
        utils.errormsg("Expected group {} to contain a single path/shape marked as the center, multiple found!".format(grp.eid))
        good = False
    else:
        center_el = center_els[0]
        center_id = center_el.eid

    # a descendant path or shape carrying the "{uri://x-plane}profile-section" marker value true
    xpth = ".//svg:*[@xplane:profile-path]"
    profile_els = grp.xpath(xpth, NSMAP)

    profile_id = '[none]'
    if len(profile_els) == 0:
        utils.errormsg("Expected group {} to contain a path/shape marked as the profile".format(grp.eid))
        good = False
    elif len(profile_els) > 1:
        utils.errormsg("Expected group {} to contain a single path/shape marked as the profile, multiple found!".format(grp.eid))
        good = False
    else:
        profile_el = profile_els[0]
        profile_id = profile_el.eid

    # add_text(self.svg, elem, self.construction_layer)
    if update_info and layer != None:
        update_section_text_for_group(svg, grp, layer,
                                      ['section #{} at {}m'.format(section_index, section_z),
                                       'center: {}'.format(center_id),
                                       'path: {}'.format(profile_id)])

    if good:
        return (True, section_index, section_z, profile_el, center_el)
    else:
        return (False, 0, 0.0, None, None)


def update_section_text_for_group(svg: SvgDocumentElement, grp: Group, layer: Layer, newtexts: List[str]):
    # find a text element in the layer with a name relating it to the group
    xpth = "svg:text[@xplane:section_group_id='{}']".format(grp.eid)
    text_els = layer.xpath(xpth, namespaces=NSMAP)

    text_el: TextElement
    bb = grp.shape_box()
    parent = grp.getparent()
    if isinstance(parent, inkex.Group):
        tx = parent.composed_transform()
    else:
        tx = inkex.Transform

    # position = inkex.Vector2d()
    position = inkex.Vector2d(bb.left, bb.bottom)
    position = tx.apply_to_point(position)

    if (len(text_els)) == 0:
        # don't have a current text element for this group
        text_el = layer.add(TextElement.new(x=position.x, y=position.y))
        text_el.set("xml:space", "preserve")
        text_el.set('{uri://x-plane}section_group_id', grp.eid)
        text_el.style = {
            "font-size": svg.viewport_to_unit("8pt"),
            "font-style": "normal",
            "font-weight": "normal",
            "line-height": "125%",
            "letter-spacing": "0px",
            "word-spacing": "0px",
            "fill": "#000000",
            "fill-opacity": 1,
            "stroke": "none",
        }
    else:
        # select the first matching text (should only be one but!)
        text_el = text_els[0]
        # remove the tspan children
        tspans = text_el.tspans()
        text_el.remove_all(Tspan)

    first_line = True
    for newtext in reversed(newtexts):
        span = text_el.add(Tspan.new(x=position.x, dx=".25em", dy="-.5em"))
        if not first_line:
            span.set('dy', "-1.2em")
        span.set("xml:space", "preserve")
        span.text = newtext
        first_line = False


def find_construction_layer(svg: SvgDocumentElement) -> Layer:
    svgNamespace = "http://www.w3.org/2000/svg"

    xpth = "//svg:g[@inkscape:groupmode = 'layer' and @xplane:name='construction_layer']"
    layers = svg.xpath(xpth, namespaces=NSMAP)

    if len(layers) == 0:
        # add a new layer
        construction_layer = Layer.new(label="construction")
        construction_layer.set('{uri://x-plane}name', 'construction_layer')
        svg.append(construction_layer)
        return construction_layer
    else:
        return layers[0]
