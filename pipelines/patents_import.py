from diagrams import Diagram, Cluster, Edge, Group
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.database import HBase
from diagrams.generic import storage
from diagrams.programming.language import Java
from diagrams.onprem.search import Solr
from diagrams.generic import compute

def java_hbase(java_label, hbase_label = "HBase"):
    java_node = Java(java_label)
    hbase_node = HBase(hbase_label)
    return java_node, hbase_node

with Diagram(name="Patents Import Details Pipeline", direction="LR" ) as diag:
    
    
    with Group(label="Import", direction="TB") as import_step:
        postgres_IFI_db = PostgreSQL("IFI DB Mirror \n XML docs")
        ifi_patent_loader, hbase_db_1 = java_hbase("ifi_claims \n IfiPatentLoader", "HBase \n +Patent")

        postgres_IFI_db >> ifi_patent_loader >> hbase_db_1

    with Group(label="NameHarmonisation") as name_harmonization_step:
        name_harmonizer_applicants, hbase_db_2 = java_hbase("name_harmonizer \n Applicants")
        name_harmonizer_intermediate_asignees, hbase_db_3 = java_hbase("name_harmonizer \n Intermediate Asignees")

        hbase_db_1 >> name_harmonizer_applicants >> hbase_db_2 >> name_harmonizer_intermediate_asignees >> hbase_db_3

    
    with Group(label="FamilyCalculation") as family_calculation_step:
        indicators_patent_family, hbase_db_4 = java_hbase("indicators_calculator \n PatentFamilyCalculator", "HBase \n +PatentFamily")
        indicators_priority_number, hbase_db_5 = java_hbase("indicators_calculator \n PatentPriorityNumberCalculator")
        indicators_family_applicants, hbase_db_6 = java_hbase("indicators_calculator \n PatentFamilyApplicantsCalculator")
        indicators_family_assignees, hbase_db_7 = java_hbase("indicators_calculator \n PatentFamilyAssigneesCalculator")

        hbase_db_3 >> indicators_patent_family >> hbase_db_4 >> indicators_priority_number >> hbase_db_5 >> indicators_family_applicants >> hbase_db_6 >> indicators_family_assignees >> hbase_db_7

    with Group(label="FlagCalculation") as flag_calculation_step:
        indicators_patent_flag, hbase_db_8 = java_hbase("indicators_calculator \n PatentsFlagsCalculator")
        indicators_patent_family_flag, hbase_db_9 = java_hbase("indicators_calculator \n PatentFamilyFlagsCalculator")

        hbase_db_7 >> indicators_patent_flag >> hbase_db_8 >> indicators_patent_family_flag >> hbase_db_9

    with Group(label="IndicatorCalculation") as indicator_calculation_step:
        indicators_patent_all, hbase_db_10 = java_hbase("indicators_calculator \n PatentsIndicatorsAll")
        hbase_db_9 >> indicators_patent_all >> hbase_db_10

    with Group(label="Solr...") as solr_steps:
        solr_indexer_patent_year_update = Java("solr_indexer \n PatentsYearUpdateToSolr")
        solr_indexer_recommendations = Java("solr_indexer \n RecommendationsPatentsByIdPrefixToSolr")
        solr_indexer_patent_num_index = Java("solr_indexer \n PatentNumberIndexToSolr")

        solr = Solr("Solr")
        hbase_db_10 >> [solr_indexer_patent_year_update, solr_indexer_recommendations, solr_indexer_patent_num_index] >> solr
    