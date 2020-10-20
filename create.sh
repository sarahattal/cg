PORT=$1
language=$2
echo $PORT
cp /home/sarahattal/Desktop/rasaProject/models/$language.tar.gz  /home/sarahattal/Desktop/models/$PORT.tar.gz
systemctl --user start nlp@$PORT.service
# echo $PORT
systemctl --user is-active --quiet nlp@$PORT.service >&1 && echo YES || echo NO