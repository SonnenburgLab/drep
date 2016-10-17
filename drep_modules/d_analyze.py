#!/usr/bin/env python3

import matplotlib
matplotlib.use('Agg')

import pandas as pd
import os
import seaborn as sns
from matplotlib import pyplot as plt
import scipy.cluster.hierarchy

# !!! This is just for testing purposes, obviously
import sys
sys.path.append('/home/mattolm/Programs/drep/')
import drep_modules as dm
import drep_modules

"""#############################################################################
                            MODULE ARCHITECTURE

****************************    Clustering   *******************************
Graphs - Heatmaps

*   plot_Mdb_heatmap(Mdb)
    -   Make a single heat-map of Mdb
    
*   plot_ANIn_heatmap(Ndb)
    -   Make a heat-map of ANIn for every MASH cluster
    
*   plot_ANIn_cov_heatmap(Ndb)
    -   Make a heat-map of ANI_alignment_coverage for every MASH cluster
    
*   plot_ANIn_clusters(Ndb, Cdb)
    -   Make a heat-map for every Ndb cluster
    
Graphs - Scatterplots

*   plot_MASH_vs_ANIn_ani(Mdb, Ndb)
    - Plot MASH_ani vs. ANIn_ani (including correlation)
    
*   plot_MASH_vs_ANIn_cov(Mdb, Ndb)
    - Plot MASH_ani vs. ANIn_cov (including correlation)
    
*   plot_ANIn_vs_ANIn_cov(Mdb, Ndb)
    - Plot ANIn vs. ANIn_cov (including correlation)
    
*   plot_MASH_vs_len(Mdb, Ndb)
    - Plot MASH_ani vs. length_difference (including correlation)
    
*   plot_ANIn_vs_len(Ndb)
    - Plot ANIn vs. length_difference (including correlation)
    
Graphs - Cluster Visualization

*   plot_MASH_clusters(Mdb, linkage, threshold (optional))
    -  Make a dengrogram and a heatmap with clusters colored
    
*   plot_ANIn_clusters(Ndb, linkage, threshold (optional))
    - For each MASH cluster, make a dendrogram and heatmap with ANIn clusters colored
    
Graphs - Custom

*   plot_cluster_tightness(Ndb)
    - Come up with some way of visualizing the variation within ANIn clusters,
      versus the variation between clusters
      - Show the average and max tightness within and between all clusters
################################################################################
"""
"""
WRAPPERS
"""

def d_analyze_wrapper(wd, **kwargs):
    
    # Load the workDirectory
    wd = drep_modules.WorkDirectory.WorkDirectory(wd)
    
    # Make the plot directory
    plot_dir = wd.location + '/figures/'
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)
        
    # Load dataframs
    Mdb = wd.get_db('Mdb')
    Ndb = wd.get_db('Ndb')
    Cdb = wd.get_db('Cdb')
    
    # Load pickles
    Mlinkage = wd.get_MASH_linkage()
    Nlinkages = wd.get_ANIn_linkages()
    
    # Load arguments
    cluster_arguments = wd.arguments['cluster']
    ML_thresh = cluster_arguments.pop('ML_thresh', 0.1)
    NL_thresh = cluster_arguments.pop('NL_thresh', 0.01)
        
    if kwargs.pop('cluster_visualization') == True:
        cluster_vis_wrapper(plot_dir, Mdb, Mlinkage, Ndb, Nlinkages, Cdb,\
                cluster_arguments, **kwargs)

def cluster_vis_wrapper(loc, Mdb, Mlinkage, Ndb, Nlinkages, Cdb, clust_args, **kwargs):
    ML_thresh = clust_args.pop('ML_thresh', 0.1)
    NL_thresh = clust_args.pop('NL_thresh', 0.01)
    
    plot_MASH_clusters(Mdb, Cdb, Mlinkage, loc= loc, threshold= ML_thresh)
    plt.clf()
    plot_ANIn_clusters(Ndb, Cdb, Nlinkages, loc= loc, threshold= NL_thresh)

"""
HEAT MAPS
"""

def plot_Mdb_heatmap(Mdb):
    db = Mdb.pivot("genome1","genome2","similarity")
    g = sns.clustermap(db,method=METHOD)
    g.fig.suptitle("MASH ANI")
    plt.setp(g.ax_heatmap.yaxis.get_majorticklabels(), rotation=0)
    return g
    
def plot_ANIn_heatmap(Ndb):
    gs = []
    for Mcluster in Ndb['MASH_cluster'].unique():
        db = Ndb[Ndb['MASH_cluster'] == Mcluster]
        if len(db['reference'].unique()) == 1:
            continue
        d = db.pivot("reference","querry","ani")
        g = sns.clustermap(d,method=METHOD)
        g.fig.suptitle("MASH cluster {0} - ANIn".format(Mcluster))
        plt.setp(g.ax_heatmap.yaxis.get_majorticklabels(), rotation=0)
        gs.append(g)
    return gs
    
def plot_ANIn_cov_heatmap(Ndb):
    gs = []
    for Mcluster in Ndb['MASH_cluster'].unique():
        db = Ndb[Ndb['MASH_cluster'] == Mcluster].copy()
        if len(db['reference'].unique()) == 1:
            continue
        d = db.pivot("reference","querry","alignment_coverage")
        g = sns.clustermap(d,method=METHOD)
        g.fig.suptitle("MASH cluster {0} - Alignment Coverage".format(Mcluster))
        plt.setp(g.ax_heatmap.yaxis.get_majorticklabels(), rotation=0)
        gs.append(g)
    return gs
    
"""
SCATTER PLOTS
"""

def plot_MASH_vs_ANIn_ani(Mdb,Ndb,exclude_zero_MASH=True):
    mdb = Mdb.copy()
    mdb.rename(columns={'genome1':'querry','genome2':'reference',
                        'similarity':'MASH_ANI'},inplace=True)
    if exclude_zero_MASH:
        mdb= mdb[mdb['MASH_ANI'] > 0]
        
    db = pd.merge(mdb,Ndb)
    db.rename(columns={'ani':'ANIn'},inplace=True)
    g = sns.jointplot(x='ANIn',y='MASH_ANI',data=db)
    return g

def plot_MASH_vs_ANIn_cov(Mdb,Ndb,exclude_zero_MASH=True):
    mdb = Mdb.copy()
    mdb.rename(columns={'genome1':'querry','genome2':'reference',
                        'similarity':'MASH_ANI'},inplace=True)
    if exclude_zero_MASH:
        mdb= mdb[mdb['MASH_ANI'] > 0]
        
    db = pd.merge(mdb,Ndb)
    db.rename(columns={'alignment_coverage':'ANIn_cov'},inplace=True)
    g = sns.jointplot(x='ANIn_cov',y='MASH_ANI',data=db)
    return g
    
def plot_ANIn_vs_ANIn_cov(Ndb):
    db = Ndb.copy()
    db.rename(columns={'alignment_coverage':'ANIn_cov','ani':'ANIn'},inplace=True)
    g = sns.jointplot(x='ANIn_cov',y='ANIn',data=db)
    return g
    
"""
CLUSETER PLOTS
"""

def plot_MASH_clusters(Mdb, Cdb, linkage, threshold= False, loc= None):
    
    db = Mdb.pivot("genome1","genome2","similarity")
    names = list(db.columns)
    name2cluster = Cdb.set_index('genome')['MASH_cluster'].to_dict()
    colors = gen_color_list(names, name2cluster)
    name2color = gen_color_dictionary(names, name2cluster)
    
    # Make the dendrogram
    g = fancy_dengrogram(linkage,names,name2color,threshold=threshold)
    plt.title('MASH clustering')
    plt.ylabel('distance (about 1 - MASH_ANI)')
    plt.ylim([0,1])
    
    # Adjust the figure size
    fig = plt.gcf()
    fig.set_size_inches(8, 10)
    plt.subplots_adjust(bottom=0.5)
    
    # Save the figure
    if loc != None:
        plt.savefig(loc + 'MASH_clustering_dendrogram.pdf')
    plt.show()
    
    
    # Make the clustermap
    g = sns.clustermap(db, row_linkage = linkage, col_linkage = linkage, \
                        row_colors = colors, col_colors = colors, vmin = 0.8, \
                        vmax = 1)
    g.fig.suptitle("MASH clustering")
    plt.setp(g.ax_heatmap.yaxis.get_majorticklabels(), rotation=0)
    
    # Adjust the figure size
    plt.subplots_adjust(bottom=0.3, right=0.7)
    
    #Save the figure
    if loc != None:
        plt.savefig(loc + 'MASH_clustering_heatmap.pdf')
    plt.show()
    

def plot_ANIn_clusters(Ndb, Cdb, cluster2linkage, threshold= False, loc= None):
    for cluster in cluster2linkage.keys():
        linkage = cluster2linkage[cluster]
        
        # Filter Ndb to just have the clusters of the linkage
        c_genomes = Cdb['genome'][Cdb['MASH_cluster'] == int(cluster)]
        db = Ndb[Ndb['reference'].isin(c_genomes)]
        db = db.pivot("reference","querry","ani")
        
        # Get the colors set up
        names = list(db.columns)
        name2cluster = Cdb.set_index('genome')['ANIn_cluster'].to_dict()
        colors = gen_color_list(names, name2cluster)
        name2color = gen_color_dictionary(names, name2cluster)
    
        # Make the dendrogram
        g = fancy_dengrogram(linkage,names,name2color,threshold=threshold)
        plt.title('ANI of MASH cluster {0}'.format(cluster))
        plt.ylabel('distance (about 1 - ANIn)')
        plt.ylim([0,0.1])
        
        # Adjust the figure size
        fig = plt.gcf()
        fig.set_size_inches(8, 10)
        plt.subplots_adjust(bottom=0.5)
        
        # Save the dendrogram
        if loc != None:
            plt.savefig(loc + 'ANIn_Mcluster{0}_dendrogram.pdf'.format(cluster))
        plt.show()

    
        # Make the clustermap
        g = sns.clustermap(db, row_linkage = linkage, col_linkage = linkage, \
                            row_colors = colors, col_colors = colors, vmin= 0.9,\
                            vmax= 1)
        g.fig.suptitle('ANI of MASH cluster {0}'.format(cluster))
        plt.setp(g.ax_heatmap.yaxis.get_majorticklabels(), rotation=0)
        
        # Adjust the figure size
        plt.subplots_adjust(bottom=0.3, right=0.7)
        
        # Save the clustermap
        if loc != None:
            plt.savefig(loc + 'ANIn_Mcluster{0}_heatmap.pdf'.format(cluster))
        plt.show()

"""
OTHER
"""

def fancy_dengrogram(linkage,names,name2color,threshold=False):
    
    # Make the dendrogram
    scipy.cluster.hierarchy.dendrogram(linkage,labels=names)
    plt.xticks(rotation=90)
    
    # Color the names
    ax = plt.gca()
    xlbls = ax.get_xmajorticklabels()
    for lbl in xlbls:
        lbl.set_color(name2color[lbl.get_text()])
        
    # Add the threshold
    if threshold:
        plt.axhline(y=threshold, c='k')
        
    g = plt.gcf()
    return g

def gen_color_list(names,name2cluster):
    '''
    Make a list of colors the same length as names, based on their cluster
    '''
    cm = plt.get_cmap('gist_rainbow')
    
    # 1. generate cluster to color
    cluster2color = {}
    clusters = set(name2cluster.values())
    NUM_COLORS = len(clusters)
    for cluster in clusters:
        try:
            cluster2color[cluster] = cm(1.*int(cluster)/NUM_COLORS)
        except:
            cluster2color[cluster] = cm(1.*int(str(cluster).split('_')[1])/NUM_COLORS)
        
    #2. generate list of colors
    colors = []
    for name in names:
        colors.append(cluster2color[name2cluster[name]])
        
    return colors
    
def gen_color_dictionary(names,name2cluster):
    '''
    Make the dictionary name2color
    '''
    cm = plt.get_cmap('gist_rainbow')
    
    # 1. generate cluster to color
    cluster2color = {}
    clusters = set(name2cluster.values())
    NUM_COLORS = len(clusters)
    for cluster in clusters:
        try:
            cluster2color[cluster] = cm(1.*int(cluster)/NUM_COLORS)
        except:
            cluster2color[cluster] = cm(1.*int(str(cluster).split('_')[1])/NUM_COLORS)
        
    #2. name to color
    name2color = {}    
    for name in names:
        name2color[name] = cluster2color[name2cluster[name]]
        
    return name2color

def gen_colors(name2cluster):
    name2color = {}
    NUM_COLORS = len(name2cluster)
    cm = plt.get_cmap('gist_rainbow')
    
    for i,tax in enumerate(taxa):
        t2c[tax] = cm(1.*i/NUM_COLORS)
    
    return t2c

def test_clustering():
    print("You should make some test cases here!")

if __name__ == '__main__':
	test_clustering()