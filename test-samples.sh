#!/usr/bin/env bash

function main {
  precheck_dir="precheck"
  samples_dir="$precheck_dir/samples"

  mkdir -p $samples_dir

  postcodes_file="$precheck_dir/sample_postcodes.txt"
  check_sample_postcodes_file $postcodes_file

  output_dir="$precheck_dir/output"

  postcodes_output_dir="$output_dir/postcodes"
  mkdir -p "$postcodes_output_dir"

  if [[ "$1" == "sample" ]]; then
    echo "Downloading sample outputs"

    for postcode in $(grep -E '^\w' $postcodes_file); do
      fetch_url "http://localhost:3108/postcode/$postcode.json" "$postcode" $samples_dir
    done
  elif [[ "$1" == "check" ]]; then
    echo "Downloading current state"

    for postcode in $(grep -E '^\w' $postcodes_file); do
      fetch_url "http://localhost:3108/postcode/$postcode.json" "$postcode" $postcodes_output_dir
    done
  fi

  if [[ "$1" == "check" ]] || [[ "$1" == "verify" ]]; then
    echo "Checking current state against sample outputs"

    for postcode in $(grep -E '^\w' $postcodes_file); do
      check_postcode "$postcode" "$samples_dir" "$postcodes_output_dir"
    done
  fi
}

function check_sample_postcodes_file {
  postcodes_file=$1

  if [ ! -f "$postcodes_file" ]; then
    mysociety_postcodes_file="https://raw.githubusercontent.com/mysociety/uk-postcode-utils/master/ukpostcodeutils/test/sample_postcodes.txt"

    echo "Missing sample postcodes file ($postcodes_file), downloading mySociety's copy"
    curl "$mysociety_postcodes_file" > "$postcodes_file"
  fi
}

function fetch_url {
  url=$1
  postcode=$2
  output_dir=$3

  # https://stackoverflow.com/a/37072904
  res=$(curl -sw "%{http_code}" "$url")
  http_code="${res:${#res}-3}"

  if [ ${#res} -eq 3 ]; then
    body=""
  else
    body="${res:0:${#res}-3}"
  fi

  mkdir "$output_dir/$postcode"
  echo -n "$http_code" > "$output_dir/$postcode/code"
  echo -n "$body" > "$output_dir/$postcode/body"
}

function check_postcode {
  postcode=$1
  expected_dir=$2
  actual_dir=$3

  if [[ ! -e "${expected_dir}/${postcode}" ]]; then
    echo "${postcode}: missing expected output"
  elif [[ ! -e "${actual_dir}/${postcode}" ]]; then
    echo "${postcode}: missing actual output"
  else
    expected_code=$(cat "${expected_dir}/${postcode}/code")
    actual_code=$(cat "${actual_dir}/${postcode}/code")

    if [[ "$expected_code" != "$actual_code" ]]; then
      echo "${postcode}: response code mismatch (expected ${expected_code} got ${actual_code})"
    fi

    diff=$(jsondiff "${expected_dir}/${postcode}/body" "${actual_dir}/${postcode}/body")
    if [[ "$diff" != "{}" ]] && [[ "$diff" != "[]" ]]; then
      echo "${postcode}: response body mismatch (got: ${diff})"
    fi
  fi
}

main "$@"
