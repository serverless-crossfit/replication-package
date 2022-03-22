# Serverless CrossFit Replication Package

This repository contains the [code](./thumbnail-generator/), [data](./data/), and [data analysis](./data-analysis/) script of the CrossFit cross-provider serverless benchmark.
It also bundles a customized extension of the [serverless benchmarker](./serverless-benchmarker/) tool to automate and analyze serverless performance experiments.

## Application

A thumbnail generator is commonly used in web applications to resize images for responsive web design across multiple devices.
The thumbnail generator application consists of two chained functions connected through an asynchronous storage bucket trigger.
More details are described in the [thumbnail-generator/README](./thumbnail-generator/README.md).

![Thumbnail Generator Architecture](./thumbnail-generator/docs/thumbnail_generator.svg)

## Replicate Data Analysis

1. Run the [data-analysis/plots.py](./data-analysis/plots.py) Python script to generate the plots and the statistical summaries presented in the paper as described in this [data-analysis/README](./data-analysis/README.md).

## Replicate Cloud Experiments

1. Run the serverless benchmarker experiment plans as described in this [experiment-plans/README](./experiment-plans/README.md) to re-run the application benchmark and collect a new dataset in the same data format as described in [data/README.md](./data/README.md).
