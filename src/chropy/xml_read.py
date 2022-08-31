"""
Useful Lattice Methods for dealing with Chroma XML files.
"""

import xml.etree.ElementTree as ET
import os
import re
import numpy as np
import pickle
import time
from tqdm import tqdm

def tree_dfs(root,f_children,f_match,verbose=False):
    """
    Given a root, and a function f_children that swallows nodes and spits out list of children,
    traverse a tree using dfs, and spit out list of nodes that satisfy f_match(node)
    
    Args:
      root (xml root): root of tree
      f_children : function from nodes, to list of children nodes
      f_match: takes in a node, spits out a bool if it matches our description
      verbose (bool): if True, will print something on every node, and be a little sleepy
    
    Returns:
      List of node matches
    """
    q = [root]; m = [];
    while q:
        n = q.pop(0)
        if verbose:
            print("Looking at node:",n)
            time.sleep(0.5)
        if f_match(n):
            m.append(n)
        q = f_children(n) + q
    return m
            

def extract_tag(xml_root,tag_name,verbose=False):
    """
    Given a root of an xml tree, find all occurences of tag_name, and return that as a list. 
    
    Args:
      xml_root: root of xml tree, as read in by pythons xml module
      tag_name: name of tag to search for 
    
    Returns:
      List of all nodes with name matching tag_name, in the xml tree. 
    """
    return tree_dfs(xml_root,list,lambda x : x.tag == tag_name,verbose=verbose)
    
def convert_tag(node,tag_type):
    """
    tag_type : "spectra_pop"
      input:
        <node>
          <spectra>..</spectra>
          ...
        </node>
      returns: list of list of complex numbers

    tag_type : "spectra"
      input:
        <node>
          <elem>
            <re>..</re>
            <im>..</im>
          </elem>
          ...
        </node>
      returns: list of complex numbers
    
    tag_type : "prop"
      input:
        <node>
          <Matrix>
            <elem  row="s0"  col="s1">
              <Matrix>
                <elem  row="c0"  col="c1"> y
                  <re>...</re>
                  <im>...</im>
                </elem>
                ...
              </Matrix>
            </elem>
            ...
          </Matrix>
        </node>
      returns: spits out a prop data structure, which is shape (3,4,3,4)
    """
    if tag_type == 'spectra_pop':
        return [[float(x[0].text) + 1j*float(x[1].text) for x in n] for n in node]
    if tag_type == 'spectra':
        return [float(x[0].text) + 1j*float(x[1].text)  if (x[0].text != '0' or x[1].text != '0') else np.nan \
                    for x in node]
    if tag_type == 'prop':
        raise NotImplementedError
        return structures.prop(np.einsum('dbca',
                       np.array([float(y[0].text) + 1j*float(y[1].text) for x in node[0] for y in x[0]]).reshape(4,4,3,3)))
    
def strip_spec_df(file_list,file_tags,meas_tags,av_file = False):
    """
    file_list : Either a list of fully qualified filenames, 
                      or just a folder name string, in which case it is assumed we are talking about those ones.
    file_tags : finv string. 
    #meas_tags : [(tag name to search in xml, tagtype e.g. 'spectra' or 'prop')]
    
    av_file : Average all data amongst each file. 
    """
    
    to_return = []
    
    #If file_list is provided a directory, read off all those files
    if type(file_list) is str:
        file_list = [file_list + x for x in os.listdir(file_list) if not x.startswith('.')]
    
    #enumerate all the files
    for i,f in enumerate(tqdm(file_list)):
        tree = ET.parse(f)
        root = tree.getroot()
        dic = finv(f.split('/')[-1],file_tags)
        df_new_base = [dic[k] for k in sorted(dic.keys())]
        for tagname,tagtype in meas_tags:
            nl = extract_tag(root,tagname)            #Extracts all the nodes that match tagname
            if av_file == True:
                all_data = []
            for j,n in enumerate(nl):
                if av_file is False:
                    df_new = df_new_base.copy()           #This will hold one new row in our dataframe
                    df_new.append(tagname)                #The tagname we are searching for in xml
                    df_new.append(j)                      #Which occurence it is 
                    df_new.append(convert_tag(n,tagtype)) #get the data
                    if df_new[-1] is None:
                        continue
                    to_return.append(df_new)              #append to dataframe
                else:
                    all_data.append(convert_tag(n,tagtype))
            if av_file is True and len(all_data) > 0:
                df_new = df_new_base.copy()
                df_new.append(tagname)
                df_new.append(np.nanmean(all_data,axis=0))
                to_return.append(df_new)
    if av_file is False:
        to_return = pd.DataFrame(to_return,columns=list(sorted(dic.keys()))+['tagname','tagoccurence','data'])
    else:
        to_return = pd.DataFrame(to_return,columns=list(sorted(dic.keys()))+['tagname','data'])
    return to_return 
   
