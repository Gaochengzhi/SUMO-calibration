rm vTypeDistributions.add.xml
python3 $SUMO_HOME/tools/createVehTypeDistribution.py veh_config/car.config.txt --size 1000 --name "car"
python3 $SUMO_HOME/tools/createVehTypeDistribution.py veh_config/truck.config.txt --size 1000 --name "truck"
sed -iE 's/.000//g' vTypeDistributions.add.xml 
rm vTypeDistributions.add.xmlE


