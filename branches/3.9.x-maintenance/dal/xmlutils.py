# -*- coding: iso-8859-1 -*-
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

import xml.etree.ElementTree
import xml.etree.cElementTree as ET

def read_attribute(xml_element, attribute_name, default_value = None):
    if attribute_name in xml_element.attrib:
        return xml_element.attrib[attribute_name]
    return default_value
    
def read_attribute_int(xml_element, attribute_name, default_value = 0):    
    val = read_attribute(xml_element, attribute_name)
    return int(val) if val is not None else default_value
    
def read_attribute_bool(xml_element, attribute_name, default_value = False):    
    val = read_attribute(xml_element, attribute_name)
    return val == 'True' if val is not None else default_value
   
def read_sub_element_text(xml_element, sub_element_name, default_value = None):
    return xml_element.find(sub_element_name).text if (xml_element.find(sub_element_name) is not None) else default_value  

def read_tag_list(xml_element):    
    tl = []
    if xml_element.find('Tags'):
        for se in xml_element.find('Tags').iter():
            if se.tag == 'Tag':
                tl.append(se.text)    
    return tl
    