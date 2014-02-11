#! /bin/sh

# This script executes several commands over a shared SSH-connection.
# It is probably a good idea to have an ssh-agent(1) running (XXX not
# anymore--should only request password once).  XXX Check again with
# notes to see that all this is sane.
#
# Note: A valid AFS token can be obtained by "kinit" followed by
# "aklog".  This avoids the "job being submitted without an AFS token"
# warning.
#
# XXX Check return status (error) on ssh/scp operations!
#
# $Id$

# Path to the chosen pyana script.  This should not need to be
# changed.  According to Marc Messerschmidt following ana-current
# should always be fine, unless one really wants to make sure
# everything is kept at the point where one started developing.  Do
# not use the shell's built-in which(1), which may give a relative
# path.
PYANA=`/usr/bin/which cxi.pyana 2> /dev/null`
if ! test -x "${PYANA}"; then
    echo "Cannot execute cxi.pyana" > /dev/stderr
    exit 1
fi

# IP-address of a random host that has the scratch directory mounted.
# psexport is preferred over psanafeh, since the latter is not
# accessible from everywhere.
NODE="psexport.slac.stanford.edu"
NODE=`host "${NODE}" | grep "has address" | head -n 1 | cut -d ' ' -f 1`

# Create a directory for temporary files and open a master connection
# to ${NODE}.  Define a function to clean it all up, and call the
# function on interrupt.  Note that the output directory is not
# removed.
tmpdir=`mktemp -d` || exit 1
ssh -fMN -o "ControlPath ${tmpdir}/control.socket" ${NODE}
NODE=`ssh -S "${tmpdir}/control.socket" ${NODE} "hostname -f"`

# This script must be run from the SIT directory, which contains the
# .sit_release file, so that the relative PYTHONPATH set by sit_setup
# is valid.  XXX Wouldn't it make sense to have
# /reg/g/psdm/etc/ana_env.sh set an absolute path?  Could find the
# user's release directory from .sit_release file and cd to it in the
# submit.sh script.  No, that's much too slow!
if ! ssh -S "${tmpdir}/control.socket" ${NODE} \
    "cd \"${PWD}\" ; relinfo > /dev/null 2>&1"; then
    echo "Must run this script from the SIT release directory" > /dev/stderr
    exit 1
fi

cleanup_and_exit() {
    ssh -O exit -S "${tmpdir}/control.socket" ${NODE} > /dev/null 2>&1
    rm -fr "${tmpdir}"
    exit ${1}
}
trap "cleanup_and_exit 1" HUP INT QUIT TERM

# The copy_phil() functions copies a phil file from ${1} to ${2}.phil.
# Included phil files are processed recursively, and written to
# ${2}.1.phil, ${2}.2.phil, ${2}.1.1.phil, etc.  Files are modified to
# reflect changes to the file names of included files.
#
# Beware!  The copy_phil() function has side effects: it changes the
# IFS as well as the working directory.
copy_phil() {
    # Return with error if source file is not readable.
    test -r "${1}" || return 1

    # Clear the internal field separator to avoid consuming leading
    # white space while reading the phil file.  Set the working
    # directory to the directory of the input file.  This emulates
    # cpp(1)-like behaviour of "include file" statements.
    IFS=""
    cd `dirname "${1}"`

    rm -f "${2}.phil"
    while read -r _line; do
        if echo "${_line}" | grep -q \
            "^[[:space:]]*include[[:space:]]\+file[[:space:]]\+"; then
            # Recursion step: replace the name of the included file
            # with a generic, safe name based on destination path.
            # Then recursively copy the included file.
            _n=`ls                             \
                | grep "^${2}\.[0-9]*\.phil\$" \
                | wc -l                        \
                | awk '{ print $0 + 1; }'`
            _dst="${2}.${_n}"
            _inc=`basename "${_dst}"`
            _src=`echo "${_line}" \
                | awk '{ $1 = $2 = ""; print substr($0, 3); }'`
            echo "include file ${_inc}.phil" >> "${2}.phil"
            copy_phil "${_src}" "${_dst}"
            cd `dirname "${1}"`
        else
            # Base case: line-by-line copy of input to output.
            echo "${_line}" >> "${2}.phil"
        fi
    done < "${1}"
}

args=`getopt c:i:o:p:q:r:st:x: $*`
if test $? -ne 0; then
    echo "Usage: lsf.sh -c config -r run-num [-i input] [-o output] [-p num-cpu] [-q queue] [-t trial] [-x exp]" > /dev/stderr
    cleanup_and_exit 1
fi

set -- ${args}
while test ${#} -ge 0; do
    case "${1}" in
        -c)
            cfg="${2}"
            if ! test -r "${cfg}" 2> /dev/null; then
                echo "config must be a readable file" > /dev/stderr
                cleanup_and_exit 1
            fi
            shift
            shift
            ;;

        -i)
            xtc=`ssh -S "${tmpdir}/control.socket" ${NODE} \
                "cd \"${PWD}\" ; readlink -fn \"${2}\""`
            if ssh -S "${tmpdir}/control.socket" ${NODE} \
                "test ! -d \"${xtc}\" 2> /dev/null"; then
                echo "${xtc} does not exist or is not a directory" > /dev/stderr
                cleanup_and_exit 1
            fi
            shift
            shift
            ;;

        -o)
            out="${2}"
            if ssh -S "${tmpdir}/control.socket" ${NODE} \
                "cd \"${PWD}\" ;                         \
                 test -e \"${out}\" -a ! -d \"${out}\" 2> /dev/null"; then
                echo "${out} exists but is not a directory" > /dev/stderr
                cleanup_and_exit 1
            fi
            ssh -S "${tmpdir}/control.socket" ${NODE}                \
                "cd \"${PWD}\" ; test -d \"${out}\" 2> /dev/null" || \
                echo "Directory ${out} will be created" > /dev/stderr
            shift
            shift
            ;;

        -p)
            if ! test "${2}" -gt 0 2> /dev/null; then
                echo "num-cpu must be positive integer" > /dev/stderr
                cleanup_and_exit 1
            fi
            nproc="${2}"
            shift
            shift
            ;;

        -q)
            queue="$2"
            shift
            shift
            ;;

        -r)
            # Set ${run} to a zero-padded, four-digit string
            # representation of the integer.
            if ! test "${2}" -ge 1 -a "${2}" -le 9999 2> /dev/null; then
                echo "run-num must be an integer in the range [1, 9999]" \
                    > /dev/stderr
                cleanup_and_exit 1
            fi
            run=`echo "${2}" | awk '{ printf("%04d", $1); }'`
            run_int=`echo "${2}"`
            shift
            shift
            ;;

        -s)
            single_host="yes"
            shift
            ;;

        -t)
            # Set ${trial} to a zero-padded, three-digit string
            # representation of the integer.
            if ! test "${2}" -ge 0 -a "${2}" -le 999 2> /dev/null; then
                echo "trial must be an integer in the range [0, 999]" \
                    > /dev/stderr
                cleanup_and_exit 1
            fi
            trial=`echo "${2}" | awk '{ printf("%03d", $1); }'`
            shift
            shift
            ;;

        -x)
            exp="${2}"
            shift
            shift
            ;;

        --)
            shift
            break
            ;;
    esac
done

# Ensure the two mandatory arguments given, and no extraneous
# arguments are present.  XXX Since the corresponding options are not
# optional, they should perhaps be positional arguments instead?
if test -z "${cfg}" -o -z "${run}"; then
    echo "Must specify -c and -r options" > /dev/stderr
    cleanup_and_exit 1
fi
if test "${#}" -gt 0; then
    echo "Extraneous arguments" > /dev/stderr
    cleanup_and_exit 1
fi

# Take ${exp} from the environment unless overridden on the command
# line, and find its absolute path.
test -n "${EXP}" -a -z "${exp}" && exp="${EXP}"
exp=`ssh -S "${tmpdir}/control.socket" ${NODE} \
    "find \"/reg/d/psdm\" -maxdepth 2 -noleaf -name \"${exp}\""`
if test -n "${exp}"; then
    if ! ssh -S "${tmpdir}/control.socket" ${NODE} \
        "test -d \"${exp}\" 2> /dev/null"; then
        echo "Could not find experiment subdirectory for ${exp}" > /dev/stderr
        cleanup_and_exit 1
    fi
fi

# Unless specified on the command line, set up the directory with the
# XTC files (i.e. the input directory) as a absolute path to a
# subdirectory of the experiment's directory.  Construct a sorted list
# of unique stream numbers for ${run}.  Explicitly consider streams
# being transferred from the DAQ (*.xtc.inprogress), but not failed
# transfers (*.xtc.inprogress.*).
test -z "${xtc}" && xtc="${exp}/xtc"
streams=`ssh -S "${tmpdir}/control.socket" ${NODE}                 \
      "ls \"${xtc}\"/e*-r${run}-s*-c*.xtc                          \
          \"${xtc}\"/e*-r${run}-s*-c*.xtc.inprogress 2> /dev/null" \
    | sed -e "s:.*-s\([[:digit:]]\+\)-c.*:\1:"                     \
    | sort -u                                                      \
    | tr -s '[:space:]' ' '`
if test -z "${streams}"; then
    echo "No streams in ${xtc}" > /dev/stderr
    cleanup_and_exit 1
fi

# If ${nproc} is not given on the the command line, fall back on
# num-cpu from ${cfg}.  Otherwise, the number of processes per host
# should be between 7 and 9 according to Marc Messerschmidt.  Using
# only two processors may decrease performance, because distributing
# data from the master process to a single worker process introduces
# overhead.
if test -z "${nproc}"; then
    nproc=`awk -F= '/^[[:space:]]*num-cpu[[:space:]]*=/ { \
                        printf("%d\n", $2);               \
                    }' "${cfg}"`
    test "${nproc}" -gt 0 2> /dev/null || nproc="7"
fi
if ! test ${nproc} != 2 2> /dev/null; then
    echo "Warning: running with two processors makes no sense" > /dev/stderr
fi

# If no queue is given on the command line then submit to default
# queue.
test -z "${queue}" && queue="psfehq"

# Unless specified on the command line, set up the output directory as
# a subdirectory named "results" within the experiment's scratch
# space.
test -z "${out}" && out="${exp}/scratch/results"
out="${out}/r${run}"

# All actual output will be written to a subdirectory for the run,
# named by its three-digit trial number.  Check that any requested
# trial number is available.  If ${trial} is not given on the command
# line, generate the next available one.
if ssh -S "${tmpdir}/control.socket" ${NODE} \
    "cd \"${PWD}\" ; test -n \"${trial}\" -a -d \"${out}/${trial}\""; then
    echo "Error: Requested trial number ${trial} already in use" > /dev/stderr
    cleanup_and_exit 1
fi

if test -z "${trial}"; then
    trial=`ssh -S "${tmpdir}/control.socket" ${NODE} \
        "cd \"${PWD}\" ;                             \
         mkdir -p \"${out}\" ;                       \
         find \"${out}\" -maxdepth 1                 \
                         -noleaf                     \
                         -name \"[0-9][0-9][0-9]\"   \
                         -printf \"%f\n\" |          \
         sort -n | tail -n 1"`
    if test -z "${trial}"; then
        trial="000"
    else
        if test "${trial}" -eq "999"; then
            echo "Error: Trial numbers exhausted" > /dev/stderr
            cleanup_and_exit 1
        fi
        trial=`expr "${trial}" \+ 1 | awk '{ printf("%03d", $1); }'`
    fi
fi
out=`ssh -S "${tmpdir}/control.socket" ${NODE} \
    "cd \"${PWD}\" ; readlink -fn \"${out}/${trial}\""`

# Copy the pyana configuration file, while substituting paths to any
# phil files, and recursively copying them, too.  Then write a
# configuration file for the analysis of each stream by substituting
# the directory names with appropriate directories in ${out}, and
# appending the stream number to the base name.  Create a run-script
# for each job, as well as a convenience script to submit all the jobs
# to the queue.  XXX If the same phil file is referenced more than
# once, there will be identical copies.  XXX Dump the environment in
# here, too?
nphil="0"
oifs=${IFS}
IFS=""
opwd=`pwd`
while read -r line; do
    if echo "${line}" | grep -q "^[[:space:]]*xtal_target[[:space:]]*="; then
        nphil=`expr "${nphil}" \+ 1`
        dst="params_${nphil}"
        src=`echo "${line}"           \
            | awk -F= '{ print $2; }' \
            | sed -e "s/^[[:space:]]*//" -e "s/[[:space:]]*\$//"`
        echo "${line}"                      \
            | awk -F= -vdst="${out}/${dst}" \
                '{ printf("%s= %s.phil\n", $1, dst); }' \
            >> "${tmpdir}/pyana.cfg"
        copy_phil "${src}" "${tmpdir}/${dst}"
    else
        echo "${line}" >> "${tmpdir}/pyana.cfg"
    fi
done < "${cfg}"
cd "${opwd}"
IFS=${oifs}

cat > "${tmpdir}/submit.sh" << EOF
#! /bin/sh

OUT="${out}"

EOF
for s in ${streams}; do
    test "X${single_host}" = "Xyes" && s="NN"
    sed -e "s:\([[:alnum:]]\+\)\(_dirname[[:space:]]*=\).*:\1\2 ${out}/\1:"    \
        -e "s:\([[:alnum:]]\+_basename[[:space:]]*=.*\)[[:space:]]*:\1s${s}-:" \
        -e "s/RUN_NO/${run_int}/g"                                             \
        -e "s:\(trial_id[[:space:]]*=\).*:\1${trial}:"                         \
        "${tmpdir}/pyana.cfg" > "${tmpdir}/pyana_s${s}.cfg"

    # Process each stream on a single host as a base-1 indexed job,
    # because base-0 will not work.  Allocate no more than ${nproc}
    # processors.  Allow the job to start if at least one processor is
    # available on the host.  Cannot use an indented here-document
    # (<<-), because that would require leading tabs which are not
    # permitted by libtbx.find_clutter.
    if test "X${single_host}" = "Xyes"; then
        job_name="r${run}"
    else
        i=`expr "${s}" \+ 1`
        job_name="r${run}[${i}]"
    fi
    cat >> "${tmpdir}/submit.sh" << EOF
bsub -J "${job_name}" -n "${nproc}" -o "\${OUT}/stdout/s${s}.out" \\
    -q "${queue}" -R "span[hosts=1]" "\${OUT}/pyana_s${s}.sh"
EOF
    # limited cores/user:  psfehq.  unlimited: psfehmpiq
    # Create the run-script for stream ${s}.  Fall back on using a
    # single processor if the number of available processors cannot be
    # obtained from the environment or is less than or equal to two.
    cat > "${tmpdir}/pyana_s${s}.sh" << EOF
#! /bin/sh

NPROC=\`printenv LSB_MCPU_HOSTS \
    | awk '{ printf("%d\n", \$2 > 2 ? \$2 : 1); }'\`
EOF

    if test "X${single_host}" = "Xyes"; then
        cat >> "${tmpdir}/pyana_s${s}.sh" << EOF
STREAMS=\`ls "${xtc}"/e*-r${run}-s*.xtc                         \
             "${xtc}"/e*-r${run}-s*.xtc.inprogress 2> /dev/null \
    | tr -s '[:space:]' ' '\`
EOF
    else
        cat >> "${tmpdir}/pyana_s${s}.sh" << EOF
STREAMS=\`ls "${xtc}"/e*-r${run}-s${s}-c*.xtc                         \
             "${xtc}"/e*-r${run}-s${s}-c*.xtc.inprogress 2> /dev/null \
    | tr -s '[:space:]' ' '\`
EOF
    fi

    cat >> "${tmpdir}/pyana_s${s}.sh" << EOF
test "\${NPROC}" -gt 2 2> /dev/null || NPROC="1"
"${PYANA}" \\
    -c "${out}/pyana_s${s}.cfg" \\
    -p "\${NPROC}" \\
    "\${STREAMS}"
EOF
    chmod 755 "${tmpdir}/pyana_s${s}.sh"
    test "X${single_host}" = "Xyes" && break
done

cp --preserve=timestamps "${cfg}" "${tmpdir}/pyana.cfg"
chmod 755 "${tmpdir}/submit.sh"

# Create all directories for the output from the analysis.  This
# eliminates a race condition when run in parallel.
directories=`awk -F=                                    \
    '/^[[:space:]]*[[:alnum:]]+_dirname[[:space:]]*=/ { \
         gsub(/^[ \t]/, "", $2);                        \
         gsub(/[ \t]$/, "", $2);                        \
         printf("\"%s\"\n", $2);                        \
     }' "${tmpdir}"/pyana_s[0-9N][0-9N].cfg | sort -u`
ssh -S "${tmpdir}/control.socket" ${NODE} \
    "echo -e \"\"${out}/stdout\"\n${directories}\" | xargs -d '\n' mkdir -p"

# Copy the configuration files and the submission script to ${out}.
# Using ls(1) causes patterns which do not match any files to expand
# to the empty string rather than the pattern itself, thus emulating
# bash(1)'s nullglob option.
scp -o "ControlPath ${tmpdir}/control.socket" -pq `ls \
    "${tmpdir}"/params_*.phil                         \
    "${tmpdir}"/pyana.cfg                             \
    "${tmpdir}"/pyana_s[0-9N][0-9N].cfg               \
    "${tmpdir}"/pyana_s[0-9N][0-9N].sh                \
    "${tmpdir}/submit.sh" 2> /dev/null` "${NODE}:${out}"
if test "${?}" -ne "0"; then
    echo "Failed to copy configuration files" > /dev/stderr
    cleanup_and_exit 1
fi

# Submit the analysis of all streams to the queueing system from
# ${NODE}.
ssh -S "${tmpdir}/control.socket" ${NODE} \
    "cd \"${PWD}\" && \"${out}/submit.sh\""

echo "Output directory: ${out}"
cleanup_and_exit 0
