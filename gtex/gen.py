"""
gen.py

Uses SraRunInfo.csv to creates manifest files and scripts for running Rail-RNA
on GTEx RNA-seq data. SraRunInfo.csv was obtained by searching SRA for the GTEx
project number, (SRP012682) AND "strategy rna seq"[Properties], as depicted in
SRA_GTEx_search_screenshot_6.37.16_PM_ET_11.21.2015.png . This returns some
mmPCR samples, which are removed from consideration in the code here.
By default, 20 batches are created. Sample labels contain gender and tissue
metadata. There are two scripts for analyzing the samples in each manifest
file: one for Rail's preprocess job flow, and the other for Rail's align job
flow.

We ran

python gen.py --s3-bucket s3://dbgap-stack-361204003210 --region us-east-1
    --c3-2xlarge-bid-price 0.25 --c3-8xlarge-bid-price 1.20
    --dbgap-key /Users/eterna/gtex/prj_8716.ngc

.

Use Rail-RNA v0.2.0 .
"""
import random
import sys
import os
from itertools import cycle
import re

if __name__ == '__main__':
    import argparse
    # Print file's docstring if -h is invoked
    parser = argparse.ArgumentParser(description=__doc__, 
                formatter_class=argparse.RawDescriptionHelpFormatter)
    # Add command-line arguments
    parser.add_argument('--s3-bucket', type=str, required=True,
            help=('path to S3 bucket in which preprocessed data and junction '
                  'data will be dumped; should be a secure bucket created '
                  'by following the instructions at '
                  'http://docs.rail.bio/dbgap/; ours was s3://rail-dbgap')
        )
    parser.add_argument('--region', type=str, required=True,
            help='AWS region in which to run job flows; we used us-east-1'
        )
    parser.add_argument('--c3-2xlarge-bid-price', type=float, required=False,
            default=0.15,
            help='bid price for each c3.2xlarge instance; this instance '
                 'type is used for preprocessing data'
        )
    parser.add_argument('--c3-8xlarge-bid-price', type=float, required=False,
            default=0.30,
            help='bid price for each c3.8xlarge instance; this instance '
                 'type is used for aligning data'
        )
    parser.add_argument('--seed', type=int, required=False,
            default=4523,
            help=('seed for random number generator; random.shuffle is used '
                  'to shuffle the GTEx samples before dividing them up into '
                  '--batch-count batches')
        )
    parser.add_argument('--run-info-path', type=str, required=False,
            default=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'SraRunInfo.csv'
                ),
            help=('path to SraRunInfo.csv generated by searching SRA '
                  'as depicted in the screenshot '
                  'SRA_GTEx_search_screenshot_6.37.16_PM_ET_11.21.2015.png')
        )
    parser.add_argument('--batch-count', type=int, required=False,
            default=20,
            help='number of batches to create; batches are designed to be '
                 'of approximately equal size'
        )
    parser.add_argument('--dbgap-key', type=str, required=True,
            help='path to dbGaP key giving access to GTEx project; this '
                 'should be an NGC file'
        )
    args = parser.parse_args()
    manifest_lines = []
    with open(args.run_info_path) as run_info_stream:
        run_info_stream.readline() # header line
        for line in run_info_stream:
            if '_rep1' in line or '_rep2' in line:
                # mmPCR sample
                continue
            tokens = line.strip().split(',')
            if tokens == ['']: break
            if int(tokens[5]) < 1000000:
                # insufficient number of spots
                continue
            manifest_lines.append('\t'.join(
                    ['dbgap:' + tokens[0], '0', 
                     '_'.join([tokens[0], tokens[26], tokens[12],
                                tokens[36],
                                re.sub('[^a-zA-Z\d:]+', '.',
                                            tokens[42].lower().strip()
                                            ).strip('.')])]
                ))
    random.seed(args.seed)
    random.shuffle(manifest_lines)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    # Write all manifest files
    manifest_streams = [open('gtex_batch_{}.manifest'.format(i), 'w')
                        for i in xrange(args.batch_count)]
    for i, manifest_stream in enumerate(cycle(manifest_streams)):
        try:
            print >>manifest_stream, manifest_lines[i]
        except IndexError:
            # No more manifest lines
            break
    for manifest_stream in manifest_streams:
        manifest_stream.close()
    # Write all prep and align scripts
    for i in xrange(args.batch_count):
        with open('prep_gtex_batch_{}.sh'.format(i), 'w') as prep_stream:
            print >>prep_stream, '#!/usr/bin/env bash'
            print >>prep_stream, (
                    'DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"'
                )
            print >>prep_stream, (
                    'rail-rna prep elastic -m $DIR/{manifest_file} '
                    '--profile dbgap --secure-stack-name dbgap '
                    '--dbgap-key {dbgap_key} --core-instance-type c3.2xlarge '
                    '--master-instance-type c3.2xlarge '
                    '-o {s3_bucket}/gtex_prep_batch_{batch_number} '
                    '-c 63 --core-instance-bid-price {core_price} '
                    '--master-instance-bid-price {core_price}'
                ).format(manifest_file='gtex_batch_{}.manifest'.format(i),
                            dbgap_key=args.dbgap_key,
                            s3_bucket=args.s3_bucket,
                            batch_number=i,
                            core_price=args.c3_2xlarge_bid_price)
        with open('align_gtex_batch_{}.sh'.format(i), 'w') as align_stream:
            print >>align_stream, '#!/usr/bin/env bash'
            print >>align_stream, (
                    'DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"'
                )
            print >>align_stream, (
                    'rail-rna align elastic -m $DIR/{manifest_file} '
                    '--profile dbgap --secure-stack-name dbgap '
                    '-o {s3_bucket} --core-instance-type c3.8xlarge '
                    '--master-instance-type c3.8xlarge '
                    '-c 80 --core-instance-bid-price {core_price} '
                    '--master-instance-bid-price {core_price} '
                    '-i {s3_bucket}/gtex_prep_batch_{batch_number} '
                    '-o {s3_bucket}/gtex_align_batch_{batch_number} '
                    '-a hg38'
                ).format(manifest_file='gtex_batch_{}.manifest'.format(i),
                            s3_bucket=args.s3_bucket,
                            batch_number=i,
                            core_price=args.c3_8xlarge_bid_price)