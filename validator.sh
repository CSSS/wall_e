#!/bin/bash

validator(){
	exitCode=$(docker inspect $1 --format='{{.State.ExitCode}}')
	echo exitCode=$exitCode
	return $exitCode
}
validator $1
