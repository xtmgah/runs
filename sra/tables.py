#!/usr/bin/env python
"""
tables.py
Abhi Nellore / December 25, 2015

Reproduces data used in Mathematica 10 notebook figures.nb for paper Human
splicing diversity across the Sequence Read Archive. Based on Nellore's talk at 
Genome Informatics 2015; see the related repo
https://github.com/nellore/gi2015.

Get and unpack HISAT 2.0.1-beta from
https://ccb.jhu.edu/software/hisat2/index.shtml; we use the tool
extract_splice_sites.py that comes with it to obtain splice sites from
annotation.

File requirements:
1. intropolis.v1.hg19.tsv.gz: database of exon-exon junctions found across
    ~21,500 SRA samples NOT PROVIDED IN THIS REPO BUT CAN BE REPRODUCED. 
    See README.md for instructions. The file is also available for download
    at http://intropolis.rail.bio .
2. intropolis.idmap.v1.hg19.tsv: maps sample indexes from
    intropolis.v1.hg19.tsv.gz to SRA run accession numbers (regex: [SED]RR\d+)
    (In this repo.)
3. All GENCODE gene annotations for GRCh37, which may be obtained by executing
    the following command.

    for i in 3c 3d 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19;
    do curl -o gencode.$i.gtf.gz
    ftp://ftp.sanger.ac.uk/pub/gencode/Gencode_human/release_$i/
    gencode.v$i.annotation.gtf.gz; if [ $? -eq 78 ];
    then curl -o gencode.$i.gtf.gz ftp://ftp.sanger.ac.uk/pub/gencode/
    Gencode_human/release_$i/gencode.v$i.annotation.GRCh37.gtf.gz;
    fi; if [ $? -eq 78 ]; then curl -o gencode.$i.gtf.gz ftp://
    ftp.sanger.ac.uk/pub/gencode/Gencode_human/release_$i/
    gencode_v$i.annotation.GRCh37.gtf.gz; fi; if [ $? -eq 78 ]; then
    curl -o gencode.$i.gtf.gz ftp://ftp.sanger.ac.uk/pub/gencode/
    release_$i/gencode.v$i.gtf.gz; fi; done

    The GENCODE GTF filenames must have the format gencode.[VERSION].gtf.gz .
    The directory containing GENCODE GTFs is specified at the command line.
4. RefSeq genes, which may be obtained by visiting the URL
    https://genome.ucsc.edu/cgi-bin/hgTables?
    hgsid=466185261_bOoa3eDIrhCkaOY4EOcXWhxm7JAj
    and downloading the refGene table of the RefSeq Genes track for hg19 
    in gzip compressed format. Output filename refGene.gtf.gz is preferred.
5. http://www.nature.com/nbt/journal/v32/n9/extref/nbt.2957-S4.zip, which
    is Supplementary Data 3 from the paper "A comprehensive assessment of
    RNA-seq accuracy, reproducibility and information content by the
    Sequencing Quality Control Consortium" by SEQC/MAQC-III Consortium
    in Nature Biotech. The junctions on this list are used to make a
    Venn Diagram.
6. The file
    http://verve.webfactional.com/misc/all_illumina_sra_for_human.tsv.gz,
    which has metadata grabbed from the SRA.
7. biosample_tags.tsv, which is in the hg19 subdirectory of this repo and was
    generated using hg19/get_biosample_data.sh . It contains metadata from the
    NCBI Biosample database, including sample submission dates.

intropolis.v1.hg19.tsv.gz is specified as argument of --junctions. Annotations
are read from arguments of command-line parameter --annotations that specify
paths to the GTFs above.

Each line of intropolis.v1.hg19.tsv.gz specifies a different junction and has
the following tab-separated fields.
1. chromosome
2. start position (1-based inclusive)
3. end position (1-based inclusive)
4. strand (+ or -)
5. 5' motif (GT, GC, or AT)
6. 3' motif (AG or AC)
7. comma-separated list of indexes of samples in which junction was found
8. comma-separated list of counts of reads overlapping junctions in
    corresponding sample from field 7. So if field 7 is 4,5,6 and field 8 is
    9,10,11 there are 9 reads overlapping the junction in the sample with
    index 4, 10 reads overlapping the junction in the sample with index 5, and
    11 reads overlapping the junction in the sample with index 6.

Each line of intropolis.idmap.v1.hg19.tsv specifies a different sample
(specifically, run) on SRA and has the following tab-separated fields.
1. sample index
2. project accession number (regex: [SED]RP\d+)
3. sample accession number (regex: [SED]RS\d+)
4. experiment accession number (regex: [SED]RX\d+)
5. run accession number (regex: [SED]RR\d+)

We used PyPy 2.5.0 with GCC 4.9.2 for our Python implementation and ran:
pypy tables.py
    --hisat2-dir /path/to/hisat2-2.0.0-beta
    --gencode-dir /path/to/directory/with/gencode/gtf.gzs
    --refgene /path/to/refGene.gtf.gz
    --junctions /path/to/intropolis.v1.hg19.tsv.gz
    --index-to-sra /path/to/intropolis.idmap.v1.hg19.tsv
    --tmp /path/to/temp_dir_with_200_GB_free_space
    --seqc /path/to/nbt.2957-S4.zip
    --sra-metadata /path/to/all_illumina_sra_for_human.tsv.gz
    --biosample-metadata /path/to/biosample_tags.tsv

Note that the argument of --hisat2-dir is the directory containing the HISAT 2
binary and extract_splice_sites.py.

The following output was obtained. It is included in this repo because this 
script cannot easily be rerun to obtain results; the input file
intropolis.v1.hg19.tsv.gz must be provided, and this requires following the
instructions in README.md for its reproduction. Note that an "overlap" below
is an instance where a junction is overlapped by a read. A read that overlaps
two exon-exon junctions contributes two overlaps (or overlap instances).

[basename].annotation_diffint.tsv
Matrix where each row is a GENCODE version i and each column is a GENCODE
version i. Each element is in the format

(|junctions in i - junctions in j|, |junctions in i and j|,
    |junctions in j - junctions in i|)

, where - is a set difference.

[basename].seqc_summary.txt
Junction counts from SEQC protocol and Rail for the 1720 samples studied by
with both. See file for details.

[basename].sample_count_submission_date_overlap_geq_20.tsv
Tab-separated fields
1. count of samples in which a given junction was found
2. count of projects in which a given junction was found
3. earliest known discovery date (in units of days after February 27, 2009)
    -- this is the earliest known submission date of a sample associated with a
    junction

Above, each junction is covered by at least 20 reads per sample.

[basename].[type].stats.tsv, where [type] is in [project, sample]
Tab-separated fields
1. [type] count
2. Number of junctions found in >= field 1 [type]s
3. Number of annotated junctions found in >= field 1 [type]s
4. Number of exonskips found in >= field 1 [type]s (exon skip: both 5' and 3'
    splice sites are annotated, but not in the same exon-exon junction)
5. Number of altstartends found in >= field 1 [type]s (altstartend: either 5'
    or 3' splice site is annotated, but not both)
6. Number of novel junctions found in >= field 1 [type]s (novel: both 5' and 
    3' splice sites are unannotated)
7. Number of GT-AG junctions found in >= field 1 [type]s
8. Number of annotated GT-AG junctions found in >= field 1 [type]s
9. Number of GC-AG junctions found in >= field 1 [type]s
10. Number of annotated GC-AG junctions found in >= field 1 [type]s
11. Number of AT-AC junctions found in >= field 1 [type]s
12. Number of annotated AT-AC junctions found in >= field 1 [type]s

[basename].seqc.stats.tsv
Tab-separated fields
1. SEQC sample count
2. Number of junctions found in >= field 1 SEQC samples
3. Number of junctions found by magic and Rail in >= field 1 SEQC samples
4. Number of junctions found by rmake and Rail in >= field 1 SEQC samples
5. Number of junctions found by subread and Rail in >= field 1 SEQC samples
6. Number of junctions found by Rail and exactly one of
    {magic, rmake, subread} in >= field 1 samples
7. Number of junctions found by Rail and exactly two of
    {magic, rmake, subread} in >= field 1 samples
8. Number of junctions found by Rail and all of {magic, rmake, subread} in
    >= field 1 samples

[basename].stats_by_sample.tsv
Tab-separated fields
1. sample index
2. project accession number
3. sample accession number
4. experiment accession number
5. run accession number
6. junction count
7. annotated junction count
8. count of junctions overlapped by at least 5 reads
9. count of annotated junctions overlapped by at least 5 reads
10. total overlap instances
11. total annotated overlap instances
"""
import sys
import gzip
import zipfile
import re
import os
import subprocess
from contextlib import contextmanager

def is_gzipped(filename):
    """ Uses gzip magic number to determine whether a file is compressed.

        filename: path to file

        Return value: True iff file filename is gzipped.
    """
    with open(filename, 'rb') as binary_input_stream:
        # Check for magic number
        if binary_input_stream.read(2) == '\x1f\x8b':
            return True
        else:
            return False

@contextmanager
def xopen(filename):
    """ Opens both gzipped and uncompressed files for contextual reading.

        filename: path to file to open

        Yield value: a gzip.open or open object
    """
    if is_gzipped(filename):
        f = gzip.open(filename)
    else:
        f = open(filename)
    try:
        yield f
    finally:
        f.close()

if __name__ == '__main__':
    import argparse
    # Print file's docstring if -h is invoked
    parser = argparse.ArgumentParser(description=__doc__, 
                formatter_class=argparse.RawDescriptionHelpFormatter)
    # Add command-line arguments
    parser.add_argument('--hisat2-dir', type=str, required=True,
            help=('path to directory containing contents of HISAT2; we '
                  'unpacked ftp://ftp.ccb.jhu.edu/pub/infphilo/hisat2/'
                  'downloads/hisat2-2.0.0-beta-Linux_x86_64.zip to get this')
        )
    parser.add_argument('--refgene', type=str, required=True,
            help='path to GTF file with RefSeq genes'
        )
    parser.add_argument('--gencode-dir', type=str, required=True,
            help='path to directory containing all GENCODE GTFs for hg19, '
                 'which includes 3c, 3d, and 4 through 19'
        )
    parser.add_argument('--junctions', type=str, required=True,
            help='junctions file; this should be intropolis.v1.hg19.tsv.gz'
        )
    parser.add_argument('--index-to-sra', type=str, required=True,
            help='index to SRA accession numbers file; this should be '
                 'intropolis.idmap.v1.hg19.tsv'
        )
    parser.add_argument('--sra-metadata', type=str, required=True,
            help='path to SRA metadata file; this should be '
                 'all_illumina_sra_for_human.tsv.gz'
        )
    parser.add_argument('--biosample-metadata', type=str, required=True,
            help='path to Biosample metadata file; this should be '
                 'biosample_tags.tsv'
        )
    parser.add_argument('--seqc', type=str, required=True,
            help='path to SEQC junctions; this should be nbt.2957-S4.zip')
    parser.add_argument('--basename', type=str, required=False,
            default='hg19',
            help='basename for output files'
        )
    args = parser.parse_args()

    from collections import defaultdict

    # Map sample indexes to accession number lines
    index_to_sra, index_to_srp, srr_to_index = {}, {}, {}
    srs_to_srr = defaultdict(list)
    # Get sample indexes for all Illumina RNA-seq from SEQC for comparison
    seqc_indexes = set()
    with xopen(args.index_to_sra) as index_stream:
        for line in index_stream:
            partitioned = line.partition('\t')
            sample_index = int(partitioned[0])
            index_to_sra[sample_index] = partitioned[2].strip()
            srp, srs, srx, srr = partitioned[2].strip().split('\t')
            srs_to_srr[srs].append(srr)
            srr_to_index[srr] = sample_index
            index_to_srp[sample_index] = srp
            if srp == 'SRP025982':
                # SEQC hit!
                seqc_indexes.add(sample_index)
    print >>sys.stderr, 'Done mapping sample indexes to samples.'

    from datetime import date
    '''For getting junctions by "earliest detection date"; use units of number
    of days after earliest date. Map sample indexes to submission dates.'''
    all_dates = {}
    with xopen(args.biosample_metadata) as biosample_stream:
        biosample_stream.readline() # header
        for line in biosample_stream:
            tokens = line.strip().split('\t')
            current_date = date(
                    *tuple(
                        [int(el.strip())
                            for el in tokens[10].split('T')[0].split('-')]
                    )
                )
            for srr in srs_to_srr[tokens[9].upper()]:
                all_dates[srr_to_index[srr]] = current_date
    earliest_date = min(all_dates.values())
    for sample_index in all_dates:
        all_dates[sample_index] = (
                all_dates[sample_index] - earliest_date
            ).days
    date_indexes = set(all_dates.keys())
    print >>sys.stderr, 'Done grabbing submission dates from Biosample DB.'

    # Grab all annotated junctions
    gencodes = defaultdict(set)
    annotated_junctions = set()
    annotated_5p = set()
    annotated_3p = set()
    refs = set(
            ['chr' + str(i) for i in xrange(1, 23)] + ['chrM', 'chrX', 'chrY']
        )
    extract_splice_sites_path = os.path.join(args.hisat2_dir,
                                                'extract_splice_sites.py')
    from glob import glob
    annotations = glob(os.path.join(args.gencode_dir, 'gencode.*.gtf.gz')) + [
                                                                args.refgene
                                                            ]
    annotations = [(os.path.basename(annotation_path), annotation_path)
                    for annotation_path in annotations]
    refgene_base = annotations[-1][0]
    for annotation_base, annotation in annotations:
        extract_process = subprocess.Popen(' '.join([
                                            sys.executable,
                                            extract_splice_sites_path,
                                            annotation
                                            if not is_gzipped(
                                               annotation
                                            ) else ('<(gzip -cd %s)'
                                               % annotation
                                            )
                                        ]),
                                        shell=True,
                                        executable='/bin/bash',
                                        stdout=subprocess.PIPE
                                    )
        if annotation_base in [refgene_base, 'gencode.19.gtf.gz']:
            for line in extract_process.stdout:
                tokens = line.strip().split('\t')
                tokens[1] = int(tokens[1]) + 2
                tokens[2] = int(tokens[2])
                if tokens[0] in refs:
                    junction_to_add = tuple(tokens[:-1])
                    annotated_junctions.add(junction_to_add)
                    if annotation_base == 'gencode.19.gtf.gz':
                        gencodes['19'].add(junction_to_add)
                    if tokens[3] == '+':
                        annotated_5p.add((tokens[0], tokens[1]))
                        annotated_3p.add((tokens[0], tokens[2]))
                    else:
                        assert tokens[3] == '-'
                        annotated_3p.add((tokens[0], tokens[1]))
                        annotated_5p.add((tokens[0], tokens[2]))
        else:
            gencode_version = annotation.split('.')[1]
            for line in extract_process.stdout:
                tokens = line.strip().split('\t')
                tokens[1] = int(tokens[1]) + 2
                tokens[2] = int(tokens[2])
                if tokens[0] in refs:
                    gencodes[gencode_version].add(tuple(tokens[:-1]))
        extract_process.stdout.close()
        exit_code = extract_process.wait()
        if exit_code != 0:
            raise RuntimeError(
                'extract_splice_sites.py had nonzero exit code {}.'.format(
                                                                    exit_code
                                                                )
            )

    gencode_versions = ['3c', '3d'] + [str(ver) for ver in range(4, 20)]
    # Write some differences/intersections
    with open(
            args.basename + '.annotation_diffint.tsv', 'w'
        ) as intersect_stream:
        print >>intersect_stream, '\t'.join([''] + gencode_versions)
        for i in gencode_versions:
            intersect_stream.write(i + '\t')
            print >>intersect_stream, '\t'.join([
                    ','.join([
                            str(len(gencodes[i] - gencodes[j])),
                            str(len(gencodes[i].intersection(gencodes[j]))),
                            str(len(gencodes[j] - gencodes[i]))])
                        for j in gencode_versions
                ])

    print >>sys.stderr, ('Found {} annotated junctions between GENCODE v19 '
                         'and refGene. Found {} annotated junctions across '
                         'GENCODE versions.').format(
                                len(annotated_junctions),
                                { version : len(gencodes[version])
                                    for version in gencodes }
                            )

    '''Grab SEQC junctions. Three protocols were used: Subread, r-make, and
    NCBI Magic.''' 
    magic_junctions, rmake_junctions, subread_junctions = set(), set(), set()
    seqc_junctions = set()
    with zipfile.ZipFile(args.seqc).open('SupplementaryData3.tab') \
        as seqc_stream:
        seqc_stream.readline() # header
        for line in seqc_stream:
            tokens = line.strip().split('\t')
            tokens[0] = tokens[0].split('.')
            junction = (tokens[0][0], int(tokens[0][1]), int(tokens[0][2]))
            add_junc = False
            if tokens[1] == '1':
                subread_junctions.add(junction)
                add_junc = True
            if tokens[2] == '1':
                rmake_junctions.add(junction)
                add_junc = True
            if tokens[3] == '1':
                magic_junctions.add(junction)
                add_junc = True
            if add_junc:
                seqc_junctions.add(junction)
    print >>sys.stderr, 'Done reading SEQC junctions.'

    # Key: sample index; value: number of junctions found in sample
    junction_counts = defaultdict(int)
    # For junctions in union of annotations specified at command line
    annotated_junction_counts = defaultdict(int)
    # Count total overlap instances and annotated overlap instances
    '''Same as above, but including only junctions covered by at least 5 reads
    in the sample.'''
    junction_counts_geq_5 = defaultdict(int)
    annotated_junction_counts_geq_5 = defaultdict(int)

    overlap_counts = defaultdict(int)
    annotated_overlap_counts = defaultdict(int)
    # Mapping counts of samples to junction counts
    sample_count_to_junction_count = defaultdict(int)
    project_count_to_junction_count = defaultdict(int)
    sample_count_to_GTAG_junction_count = defaultdict(int)
    project_count_to_GTAG_junction_count = defaultdict(int)
    sample_count_to_GCAG_junction_count = defaultdict(int)
    project_count_to_GCAG_junction_count = defaultdict(int)
    sample_count_to_ATAC_junction_count = defaultdict(int)
    project_count_to_ATAC_junction_count = defaultdict(int)
    sample_count_to_GTAG_ann_count = defaultdict(int)
    project_count_to_GTAG_ann_count = defaultdict(int)
    sample_count_to_GCAG_ann_count = defaultdict(int)
    project_count_to_GCAG_ann_count = defaultdict(int)
    sample_count_to_ATAC_ann_count = defaultdict(int)
    project_count_to_ATAC_ann_count = defaultdict(int)
    # One of 5' or 3' splice site is in annotation, one isn't
    sample_count_to_altstartend_junction_count = defaultdict(int)
    project_count_to_altstartend_junction_count = defaultdict(int)
    # Both 5' and 3' splice sites are in annotation, but junction is not
    sample_count_to_exonskip_junction_count = defaultdict(int)
    project_count_to_exonskip_junction_count = defaultdict(int)
    # Full junction is in annotation
    sample_count_to_annotated_junction_count = defaultdict(int)
    project_count_to_annotated_junction_count = defaultdict(int)
    # Neither 5' nor 3' is in annotation
    sample_count_to_novel_junction_count = defaultdict(int)
    project_count_to_novel_junction_count = defaultdict(int)
    # For comparison wth SEQC
    rail_seqc_junctions = set()
    seqc_sample_count_to_junction_count = defaultdict(int)
    seqc_sample_count_to_magic = defaultdict(int)
    seqc_sample_count_to_rmake = defaultdict(int)
    seqc_sample_count_to_subread = defaultdict(int)
    seqc_sample_count_to_ones = defaultdict(int)
    seqc_sample_count_to_twos = defaultdict(int)
    seqc_sample_count_to_threes = defaultdict(int)
    # For junction-date analyses
    date_to_junction_count = defaultdict(int)
    date_to_junction_count_overlap_geq_20 = defaultdict(int)

    with xopen(args.junctions) as junction_stream, gzip.open(
            args.basename
            + '.sample_count_submission_date_overlap_geq_20.tsv.gz', 'w'
        ) as junction_date_stream:
        print >>junction_date_stream, ((
                               '# reads across samples in which junction '
                               'was found\t'
                               '# samples in which junction was found'
                               '\t# projects in which junction was found'
                               '\tearliest known discovery date in '
                               'days after %s; format Y-M-D\t') % (
                                        earliest_date.strftime(
                                            '%Y-%m-%d'
                                        )
                                    )) + '\t'.join(
                                        ['present in GENCODE v' + ver
                                            for ver in gencode_versions]
                                    ) + '\tearliest GENCODE version'
        for line in junction_stream:
            tokens = line.strip().split('\t')
            junction = (tokens[0], int(tokens[1]), int(tokens[2]))
            if tokens[3] == '+':
                fivep = junction[:2]
                threep = (junction[0], junction[2])
            elif tokens[3] == '-':
                threep = junction[:2]
                fivep = (junction[0], junction[2])
            else:
                raise RuntimeError('Bad strand in line "%s"' % line)
            samples = [int(el) for el in tokens[-2].split(',')]
            coverages = [int(el) for el in tokens[-1].split(',')]
            sample_count = len(samples)
            project_count = len(set([index_to_srp[sample]
                                        for sample in samples]))
            try:
                discovery_date = min(
                        [all_dates[sample] for sample in samples
                            if sample in date_indexes]
                    )
            except ValueError:
                # No discovery date available!
                pass
            else:
                date_to_junction_count[discovery_date] += 1
                cov_sum = sum(coverages)
                if cov_sum >= 20:
                    date_to_junction_count_overlap_geq_20[discovery_date] += 1
                    gencode_bools_to_print = [
                            '1' if junction in gencodes[ver]
                            else '0' for ver in gencode_versions
                        ]
                    try:
                        earliest_gencode_version = gencode_versions[
                                gencode_bools_to_print.index('1')
                            ]
                    except ValueError:
                        earliest_gencode_version = 'NA'
                    print >>junction_date_stream, ('%d\t%d\t%d\t%d\t' % (
                                cov_sum,
                                sample_count,
                                project_count,
                                discovery_date
                        )) + '\t'.join(gencode_bools_to_print) + (
                            '\t' + earliest_gencode_version
                        ) 
            samples_and_coverages = zip(samples, coverages)
            sample_count_to_junction_count[sample_count] += 1
            project_count_to_junction_count[project_count] += 1
            if tokens[5] == 'AG':
                if tokens[4] == 'GT':
                    sample_count_to_GTAG_junction_count[sample_count] += 1
                    project_count_to_GTAG_junction_count[project_count] += 1
                elif tokens[4] == 'GC':
                    sample_count_to_GCAG_junction_count[sample_count] += 1
                    project_count_to_GCAG_junction_count[project_count] += 1
                else:
                    raise RuntimeError('Bad motif in line "%s"' % line)
            elif tokens[5] == 'AC':
                if tokens[4] == 'AT':
                    sample_count_to_ATAC_junction_count[sample_count] += 1
                    project_count_to_ATAC_junction_count[project_count] += 1
                else:
                    raise RuntimeError('Bad motif in line "%s"' % line)
            if junction in annotated_junctions:
                sample_count_to_annotated_junction_count[sample_count] += 1
                project_count_to_annotated_junction_count[project_count] += 1
                if tokens[5] == 'AG':
                    if tokens[4] == 'GT':
                        sample_count_to_GTAG_ann_count[sample_count] += 1
                        project_count_to_GTAG_ann_count[project_count] += 1
                    elif tokens[4] == 'GC':
                        sample_count_to_GCAG_ann_count[sample_count] += 1
                        project_count_to_GCAG_ann_count[project_count] += 1
                elif tokens[5] == 'AC':
                    sample_count_to_ATAC_ann_count[sample_count] += 1
                    project_count_to_ATAC_ann_count[project_count] += 1
                for sample, coverage in samples_and_coverages:
                    annotated_junction_counts[sample] += 1
                    annotated_overlap_counts[sample] += coverage
                    if coverage >= 5:
                        annotated_junction_counts_geq_5[sample] += 1
            elif threep in annotated_3p:
                if fivep in annotated_5p:
                    sample_count_to_exonskip_junction_count[sample_count] += 1
                    project_count_to_exonskip_junction_count[
                            project_count
                        ] += 1
                else:
                    sample_count_to_altstartend_junction_count[sample_count] \
                        += 1
                    project_count_to_altstartend_junction_count[
                            project_count
                        ] += 1
            elif fivep in annotated_5p:
                sample_count_to_altstartend_junction_count[sample_count] += 1
                project_count_to_altstartend_junction_count[project_count] += 1
            else:
                sample_count_to_novel_junction_count[sample_count] += 1
                project_count_to_novel_junction_count[project_count] += 1
            seqc_intersect = set(samples).intersection(seqc_indexes)
            if seqc_intersect:
                rail_seqc_junctions.add(junction)
                seqc_sample_count = len(seqc_intersect)
                seqc_sample_count_to_junction_count[seqc_sample_count] += 1
                intersect_count = 0
                if junction in magic_junctions:
                    seqc_sample_count_to_magic[seqc_sample_count] += 1
                    intersect_count += 1
                if junction in rmake_junctions:
                    seqc_sample_count_to_rmake[seqc_sample_count] += 1
                    intersect_count += 1
                if junction in subread_junctions:
                    seqc_sample_count_to_subread[seqc_sample_count] += 1
                    intersect_count += 1
                if intersect_count == 1:
                    seqc_sample_count_to_ones[seqc_sample_count] += 1
                elif intersect_count == 2:
                    seqc_sample_count_to_twos[seqc_sample_count] += 1
                elif intersect_count == 3:
                    seqc_sample_count_to_threes[seqc_sample_count] += 1
            for sample, coverage in samples_and_coverages:
                junction_counts[sample] += 1
                overlap_counts[sample] += coverage
                if coverage >= 5:
                    junction_counts_geq_5[sample] += 1
    print >>sys.stderr, 'Done reading junction file.'

    '''Aggregate junction stats: how many junctions/overlaps of given type
    are found in >= K samples/projects/seqc samples?'''
    sample_stats_to_aggregate = [sample_count_to_junction_count,
                                 sample_count_to_annotated_junction_count,
                                 sample_count_to_exonskip_junction_count,
                                 sample_count_to_altstartend_junction_count,
                                 sample_count_to_novel_junction_count,
                                 sample_count_to_GTAG_junction_count,
                                 sample_count_to_GTAG_ann_count,
                                 sample_count_to_GCAG_junction_count,
                                 sample_count_to_GCAG_ann_count,
                                 sample_count_to_ATAC_junction_count,
                                 sample_count_to_ATAC_ann_count]
    project_stats_to_aggregate = [project_count_to_junction_count,
                                  project_count_to_annotated_junction_count,
                                  project_count_to_exonskip_junction_count,
                                  project_count_to_altstartend_junction_count,
                                  project_count_to_novel_junction_count,
                                  project_count_to_GTAG_junction_count,
                                  project_count_to_GTAG_ann_count,
                                  project_count_to_GCAG_junction_count,
                                  project_count_to_GCAG_ann_count,
                                  project_count_to_ATAC_junction_count,
                                  project_count_to_ATAC_ann_count]
    seqc_stats_to_aggregate = [seqc_sample_count_to_junction_count,
                                seqc_sample_count_to_magic,
                                seqc_sample_count_to_rmake,
                                seqc_sample_count_to_subread,
                                seqc_sample_count_to_ones,
                                seqc_sample_count_to_twos,
                                seqc_sample_count_to_threes]
    header_prototype = ('min {descriptor}s\t'
                          'junctions\t'
                          'annotated\t'
                          'exonskips\t'
                          'altstartend\t'
                          'novel\t'
                          'GTAG\t'
                          'annotated GTAG\t'
                          'GCAG\t'
                          'annotated GCAG\t'
                          'ATAC\t'
                          'annotated ATAC')
    seqc_header = ('min seqc samples\t'
                      'junctions\t'
                      'magic junctions\t'
                      'rmake junctions\t'
                      'subread junctions\t'
                      'exactly one of {magic, rmake, subread} junctions\t'
                      'exactly two of {magic, rmake, subread} junctions\t'
                      'all three of {magic, rmake, subread} junctions')
    for stats, header, descriptor in [
                          (sample_stats_to_aggregate,
                                header_prototype.format(descriptor='sample'),
                                'sample'),
                          (project_stats_to_aggregate,
                                header_prototype.format(descriptor='project'),
                                'project'),
                          (seqc_stats_to_aggregate,
                                seqc_header,
                                'seqc_sample')
                        ]:
        max_count, min_count = 0, 1000000000 # way larger than max # samples
        for stat in stats:
            max_count = max(stat.keys() + [max_count])
            min_count = min(stat.keys() + [min_count])
        stat_count = len(stats)
        stat_aggregators = [0 for _ in xrange(stat_count)]
        with open(args.basename + '.' + descriptor + '.stats.tsv', 'w') \
            as stat_stream:
            print >>stat_stream, header
            for descriptor_count in xrange(max_count, min_count - 1, -1):
                for i in xrange(stat_count):
                    stat_aggregators[i] += stats[i][descriptor_count]
                print >>stat_stream, '\t'.join(
                                    [str(descriptor_count)]
                                    + [str(el) for el in stat_aggregators]
                                )

    print >>sys.stderr, ('Dumped sample/project-level and SEQC '
                         'aggregate junction stats.')

    # Dump junction information by sample
    with open(args.basename + '.stats_by_sample.tsv', 'w') as stat_stream:
        print >>stat_stream, ('sample index\tproject\tsample\texperiment\trun'
                              '\tjunctions\tannotated_junctions'
                              '\tjunctions_geq_5\tannotated_junctions_geq_5'
                              '\toverlaps\tannotated_overlaps')
        for sample_index in sorted(index_to_sra.keys()):
            print >>stat_stream, '\t'.join(
                        [str(el) for el in 
                            [sample_index, index_to_sra[sample_index],
                                junction_counts[sample_index],
                                annotated_junction_counts[sample_index],
                                junction_counts_geq_5[sample_index],
                                annotated_junction_counts_geq_5[sample_index],
                                overlap_counts[sample_index],
                                annotated_overlap_counts[sample_index]]]
                    )
    print >>sys.stderr, 'Dumped junction info by sample.'

    # SEQC summary
    with open(args.basename + '.seqc_summary.txt', 'w') as seqc_stream:
        in_all = set.intersection(
                        magic_junctions, rmake_junctions, subread_junctions
                    )
        in_one = set.union(
                        magic_junctions, rmake_junctions, subread_junctions
                    )
        in_two = set.union(
                    set.intersection(magic_junctions, rmake_junctions),
                    set.intersection(magic_junctions, subread_junctions),
                    set.intersection(rmake_junctions, subread_junctions)
                )
        print >>seqc_stream, (
                'total samples studied by SEQC consortium and Rail: %d'
                    % len(seqc_indexes)
            )
        print >>seqc_stream, (
                'junctions found by magic, rmake, and subread: %d'
                    % len(in_all)
            )
        print >>seqc_stream, (
                'junctions found by magic, rmake, or subread: %d'
                    % len(in_one)
            )
        print >>seqc_stream, (
                'junctions found by at least two of '
                '[magic, rmake, subread]: %d'
            ) % len(in_two)
        print >>seqc_stream, (
                'junctions found by Rail: %d' % len(rail_seqc_junctions)
            )

    print >>sys.stderr, 'Dumped SEQC summary.'