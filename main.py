from pyspark.sql import SparkSession
from pyspark.sql.functions import col

class AnalysisApp:
    def __init__(self, spark):
        self.spark = spark
        self.data = self.load_data()

    def load_data(self):
        charges = self.spark.read.csv("BCG-Case-study/code/src/Data/Charges_use.csv", header=True, inferSchema=True)
        endorsements = self.spark.read.csv("/home/rac/Documents/case_study/BCG-Case-study/Data/Endorse_use.csv", header=True, inferSchema=True)
        restrict = self.spark.read.csv("/home/rac/Documents/case_study/BCG-Case-study/Data/Restrict_use.csv", header=True, inferSchema=True)
        damages = self.spark.read.csv("/home/rac/Documents/case_study/BCG-Case-study/Data/Damages_use.csv", header=True, inferSchema=True)
        primary_person = self.spark.read.csv("/home/rac/Documents/case_study/BCG-Case-study/Data/Primary_Person_use.csv", header=True, inferSchema=True)
        unit = self.spark.read.csv("/home/rac/Documents/case_study/BCG-Case-study/Data/Units_use.csv", header=True, inferSchema=True)

        return {
            "charges": charges,
            "endorsements": endorsements,
            "restrict": restrict,
            "damages": damages,
            "primary_person": primary_person,
            "unit": unit
        }

    def analysis_1(self):
        # Find the number of crashes in which the number of males killed is greater than 2
        result = self.data["primary_person"].filter(
            (col("PRSN_GNDR_ID") == "MALE") & (col("TOT_INJRY_CNT") > 2)
        ).select("CRASH_ID").distinct().count()

        print("Analysis 1 Result:", result)

    def analysis_2(self):
        # Count the number of two-wheelers booked for crashes
        result = self.data["unit"].filter(col("UNIT_DESC_ID") == "MOTOR VEHICLE").count()

        print("Analysis 2 Result:", result)

    def analysis_3(self):
        # Determine the Top 5 Vehicle Makes of the cars in crashes where the driver died and Airbags did not deploy
        result = self.data["unit"].join(
            self.data["primary_person"],
            ["CRASH_ID", "UNIT_NBR"],
            "inner"
        ).filter(
            (col("PRSN_INJRY_SEV_ID") == "INCAPACITATING INJURY") & (col("PRSN_AIRBAG_ID") == "NOT DEPLOYED")
        ).groupBy("VEH_MAKE_ID").count().orderBy(col("count").desc()).limit(5)

        print("Analysis 3 Result:")
        result.show()

    def analysis_4(self):
        # Determine the number of vehicles with drivers having valid licenses involved in hit and run
        result = self.data["primary_person"].join(
            self.data["charges"],
            ["CRASH_ID", "UNIT_NBR"],
            "inner"
        ).filter(
            (col("CHARGE") == "ACCIDENT HIT AND RUN") & (col("DRVR_LIC_TYPE_ID")== "DRIVER LICENSE")
        ).select("CRASH_ID").distinct().count()

        print("Analysis 4 Result:", result)

    def analysis_5(self):
        # Find the state with the highest number of accidents where females are not involved
        result = self.data["primary_person"].filter(
            (col("PRSN_GNDR_ID") != "FEMALE")
        ).groupBy("DRVR_LIC_STATE_ID").count().orderBy(col("count").desc()).limit(1)

        print("Analysis 5 Result:")
        result.show()

    def analysis_6(self):
        # Determine the Top 3rd to 5th VEH_MAKE_IDs that contribute to the largest number of injuries including death
        unit_df = self.data["unit"].withColumnRenamed("TOT_INJRY_CNT", "unit_TOT_INJRY_CNT")
        primary_person_df = self.data["primary_person"].withColumnRenamed("TOT_INJRY_CNT", "person_TOT_INJRY_CNT")

        # Perform the join using the aliased columns
        result = unit_df.join(
            primary_person_df,
            ["CRASH_ID", "UNIT_NBR"],
            "inner"
        ).groupBy("VEH_MAKE_ID").agg(
            {"person_TOT_INJRY_CNT": "sum"}
        ).withColumnRenamed("sum(person_TOT_INJRY_CNT)", "total_injuries").orderBy(col("total_injuries").desc()).limit(3)

        print("Analysis 6 Result:")
        result.show()

    def analysis_7(self):
        # For all body styles involved in crashes, mention the top ethnic user group of each unique body style
        result = self.data["unit"].join(
            self.data["primary_person"],
            ["CRASH_ID", "UNIT_NBR"],
            "inner"
        ).groupBy("VEH_BODY_STYL_ID", "PRSN_ETHNICITY_ID").count().orderBy(
            col("VEH_BODY_STYL_ID"), col("count").desc()
        ).groupBy("VEH_BODY_STYL_ID").agg(
            {"PRSN_ETHNICITY_ID": "first"}
        )

        print("Analysis 7 Result:")
        result.show()

    def analysis_8(self):

        joined_df = self.data["unit"].join(
            self.data["charges"],
            ["CRASH_ID", "UNIT_NBR"],
            "inner"
        ).join(
            self.data["primary_person"],
            ["CRASH_ID", "UNIT_NBR"],
            "inner"
        )

        # Filter by alcohol-related crashes
        filtered_df = joined_df.filter(
            col("CONTRIB_FACTR_1_ID").contains("UNDER INFLUENCE - ALCOHOL")
        )

        # Group by DRVR_ZIP and find the Top 5 Zip Codes with the highest number of crashes
        result = filtered_df.groupBy("DRVR_ZIP").count().orderBy(col("count").desc()).limit(5)

        print("Analysis 8 Result:")
        result.show()

    def analysis_9(self):
        # Count of Distinct Crash IDs where No Damaged Property was observed, Damage Level is above 4, and car avails Insurance
        result = self.data["damages"].join(
            self.data["unit"],
            ["CRASH_ID"],
            "inner"
        ).filter(
            (col("DAMAGED_PROPERTY").isNull()) & (col("VEH_DMAG_SCL_1_ID") == "DAMAGED 4") 
        ).select("CRASH_ID").distinct().count()

        print("Analysis 9 Result:", result)

    def analysis_10(self):
        # Determine the Top 5 Vehicle Makes where drivers are charged with speeding-related offences, have licensed Drivers,
        # use top 10 vehicle colors, and have cars licensed with the Top 25 states with the highest number of offences
        result = self.data["unit"].join(
            self.data["charges"],
            ["CRASH_ID"],
            "inner"
        ).filter(
            (col("CHARGE").contains("FAIL TO CONTROL SPEED"))  &
            (col("VEH_COLOR_ID").isin(["BGE", "BLK", "BLU", "BRO", "BRZ", "CAM", "CPR", "GLD", "GRY", "MAR"])) 
        ).groupBy("VEH_MAKE_ID").count().orderBy(col("count").desc()).limit(5)

        print("Analysis 10 Result:")
        result.show()

    # ... (Code to call other analysis functions)

if __name__ == "__main__":
    spark = SparkSession.builder.appName("CaseStudyApp").getOrCreate()

    # Create an instance of the AnalysisApp class
    analysis_app = AnalysisApp(spark)

    # Perform analyses
    analysis_app.analysis_1()
    analysis_app.analysis_2()
    analysis_app.analysis_3()
    analysis_app.analysis_4()
    analysis_app.analysis_5()
    analysis_app.analysis_6()
    analysis_app.analysis_7()
    analysis_app.analysis_8()
    analysis_app.analysis_9()
    analysis_app.analysis_10()
    spark.stop()
