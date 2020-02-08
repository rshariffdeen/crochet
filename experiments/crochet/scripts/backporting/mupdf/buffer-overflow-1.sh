bug_id=buffer-overflow
project_name=mupdf
dir_name=$1/backport/$project_name/$bug_id
dir_name_docker=/data/backport/$project_name/$bug_id

project_url=https://github.com/ArtifexSoftware/mupdf.git
pa=$project_name-1.11
pb=$project_name-1.11.1
pc=$project_name-1.7

pa_commit=34e18d1
pb_commit=06a012a4
pc_commit=1.7


mkdir -p $dir_name
cd $dir_name
git clone $project_url $pa
cp -rf $pa $pb
cp -rf $pa $pc
cd $pa
git checkout $pa_commit

cd ../$pb
git checkout $pb_commit

cd ../$pc
git checkout $pc_commit

docker exec patchweave bash -c "cd $dir_name_docker/$pc;git submodule update --init"
docker exec patchweave bash -c "cd $dir_name_docker/$pc; bear make"
docker exec patchweave python /patchweave/script/format.py $dir_name_docker/$pc
git add *.c
git commit -m "format style"
git reset --hard HEAD

