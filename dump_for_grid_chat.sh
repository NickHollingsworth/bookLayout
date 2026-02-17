for i in tools/style/style.css tools/templates/page.html #tools/preprocess.conf
do
	echo ""
	echo ""
	echo "File ${i}:"
	echo "----------"
	cat ${i}
done
