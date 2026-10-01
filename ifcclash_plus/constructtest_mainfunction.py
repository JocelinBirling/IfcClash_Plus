import RuleClass
from RuleClass import SelectFacet,SelectRule,RuleFile
from Rules import Volume, Area, TopOrBottomSurface,Intersection,Above,OBB_Above,Ray_Check,OBB_Below
from ifctester import ids
from ifcopenshell import file
import ifcopenshell



def Test_Folder():
    Chemin = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
    OneRuleFile = RuleClass.RuleFile()
    OneRuleFile.list_ifc_path= [Chemin]

    Source_Select = SelectFacet()
    Source_Facet = ids.Entity(name="IFCWALLSTANDARDCASE")
    Source_Select.applicability = [Source_Facet]
    Source_Select.list_ifc_path = [Chemin]

    Target_Select = SelectFacet()
    Target_Facet = ids.Entity(name="IFCWINDOW")
    Target_Select.applicability = [Target_Facet]
    Target_Select.list_ifc_path = [Chemin]


    rule1 = Above(source=Source_Select, target=Target_Select,tolerance=1,above_type="Above_MaxToMax")
    rule2 = Above(source=Source_Select, target=Target_Select,tolerance=1,above_type="Above_MaxToMax")
    rule3 = Above(source=Source_Select, target=Target_Select,tolerance=1,above_type="Above_MaxToMax")
    rule4 = Above(source=Source_Select, target=Target_Select,tolerance=1,above_type="Above_MaxToMax")

    OneFolder1 = RuleClass.RuleFolder()
    OneFolder1_1 = RuleClass.RuleFolder()
    OneFolder1_2 = RuleClass.RuleFolder()


    OneFolder1_1.contains = [rule1,rule2]
    OneFolder1_2.contains = [rule3,rule4]

    OneFolder1.contains = [OneFolder1_1, OneFolder1_2]
    OneRuleFile.contains = [OneFolder1]

    OneRuleFile.run()


def Volume_Check():
    Chemin = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
    OneSelect_Facet = SelectFacet()
    Wall_Facet = ids.Entity(name="IFCWALLSTANDARDCASE")
    OneSelect_Facet.applicability = [Wall_Facet]
    OneSelect_Facet.list_ifc_path = [Chemin]

    rulevolume = Volume(OneSelect_Facet, 1, 2)
    rulevolume.run()

    print("Sucess", rulevolume.sucess)
    print("Fail", rulevolume.fail)


def Exception_Check():
    Chemin = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
    OneSelect_Facet = SelectFacet()
    Wall_Facet = ids.Entity(name="IFCWALLSTANDARDCASE")
    OneSelect_Facet.applicability = [Wall_Facet]
    OneSelect_Facet.list_ifc_path = [Chemin]

    rulevolume = Volume(OneSelect_Facet, 1, 2)
    ruleArea = Volume(OneSelect_Facet, 0, 2)

    rulevolume.select_exception = [ruleArea]
    rulevolume.run()


def Grouping_Test():
    Chemin = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
    OneSelect_Facet = SelectFacet()
    Wall_Facet = ids.Entity(name="IFCWALLSTANDARDCASE")
    OneSelect_Facet.applicability = [Wall_Facet]
    OneSelect_Facet.list_ifc_path = [Chemin]

    rulevolume = Volume(OneSelect_Facet, 1, 2)
    rulevolume.grouping = "ENTITY"

    rulevolume.run()
    for x in rulevolume.result:
        print(x.source_group, x.source)

def Actor_And_Criticity_Test():
    Chemin = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"

    WallStandardCase_Facet = ids.Entity(name="IFCWALLSTANDARDCASE")
    Wall_Facet = ids.Entity(name="IFCWALL")

    OneSelect_Facet = SelectFacet()
    OneSelect_Facet.applicability = [WallStandardCase_Facet]
    OneSelect_Facet.list_ifc_path = [Chemin]

    select_actor = SelectFacet()
    select_actor.classification_name = "Jean"
    select_actor.applicability = [WallStandardCase_Facet]

    select_criticity = SelectFacet()
    select_criticity.classification_name = "High"
    select_criticity.applicability = [WallStandardCase_Facet]

    rulevolume = Volume(OneSelect_Facet, 1, 2)
    rulevolume.grouping = "ENTITY"
    rulevolume.select_actor = select_actor
    rulevolume.select_criticity = select_criticity

    rulevolume.run()
    for x in rulevolume.result:
        print(x.source_group, x.status, x.actor, x.criticity, x.source)

def Top_Surface():
    Chemin = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"

    WallStandardCase_Facet = ids.Entity(name="IFCWALLSTANDARDCASE")
    Wall_Facet = ids.Entity(name="IFCWALL")

    OneSelect_Facet = SelectFacet()
    OneSelect_Facet.applicability = [WallStandardCase_Facet]
    OneSelect_Facet.list_ifc_path = [Chemin]

    rulevolume = TopSurface(OneSelect_Facet, 1, 2)

    rulevolume.run()

def IntersectionCheck():
    Chemin = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
    Wall_Select = SelectFacet()
    Wall_Facet = ids.Entity(name="IFCWALLSTANDARDCASE")
    Wall_Select.applicability = [Wall_Facet]
    Wall_Select.list_ifc_path = [Chemin]

    Window_Select = SelectFacet()
    Window_Facet = ids.Entity(name="IFCWINDOW")
    Window_Select.applicability = [Window_Facet]
    Window_Select.list_ifc_path = [Chemin]

    rulevolume = Intersection(Window_Select, Wall_Select,0.01)

    exception_rule = Intersection(None,None,0.1)
    select_rule=SelectRule()
    select_rule.rule=exception_rule


    rulevolume.select_exception=[select_rule]
    rulevolume.run()

def ExceptionMakinProcess():
    from RuleClass import Select
    Chemin = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
    ifc_file=ifcopenshell.open(Chemin)

    ifc_window=ifc_file.by_guid("1hOSvn6df7F8_7GcBWlS_W")
    ifc_wall=ifc_file.by_guid("2O2Fr$t4X7Zf8NOew3FLOH")



    exception_rule = Intersection(None,None,0.01)

    exception_rule.select_source=Select()
    exception_rule.select_source.dict_elements={ifc_wall.file:[ifc_wall]}
    exception_rule.select_source.list_ifc_file=[ifc_wall.file]
    exception_rule.select_target=Select()
    exception_rule.select_target.dict_elements={ifc_window.file:[ifc_window]}
    exception_rule.select_target.list_ifc_file=[ifc_window.file]

    Resultat=exception_rule.run()

    for key,value in exception_rule.__dict__.items():
        print(key,value)

    print("Les Resulstas")
    print(exception_rule.result[0].__dict__)


def OneElement():
    Chemin = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
    import ifcopenshell
    ifc_file=ifcopenshell.open(Chemin)

    ifc_wall=ifc_file.by_type("IFCWALL")

def AboveConstruct():

    Chemin = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
    OneRuleFile = RuleClass.RuleFile()
    OneRuleFile.list_ifc_path= [Chemin]

    Chemin = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
    Source_Select = SelectFacet()
    Source_Facet = ids.Entity(name="IFCWALLSTANDARDCASE")
    Source_Select.applicability = [Source_Facet]


    Target_Select = SelectFacet()
    Target_Facet = ids.Entity(name="IFCWINDOW")
    Target_Select.applicability = [Target_Facet]

    rule = Above(source=Source_Select, target=Target_Select,tolerance=1,above_type="Above_MaxToMax")

    OneRuleFile.contains=[rule]


    OneRuleFile.run()


    for one_result in OneRuleFile.contains[0].result:
        print(one_result)


def Criticity():
    Chemin = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
    Source_Select = SelectFacet()
    Source_Facet = ids.Entity(name="IFCWALLSTANDARDCASE")
    Source_Select.applicability = [Source_Facet]


    Target_Select = SelectFacet()
    Target_Facet = ids.Entity(name="IFCWINDOW")
    Target_Select.applicability = [Target_Facet]


    Source_Select_Criticy = SelectFacet()
    Source_Facet = ids.Entity(name="IFCWALLSTANDARDCASE")
    Source_Select_Criticy.applicability = [Source_Facet]
    Source_Select_Criticy.classification_name="Mur"


    Chemin = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
    OneRuleFile = RuleClass.RuleFile()
    OneRuleFile.list_ifc_path= [Chemin]



    rule = Above(source=Source_Select, target=Target_Select,tolerance=1,above_type="Above_MaxToMax")
    rule.select_criticity=[Source_Select_Criticy]
    OneRuleFile.contains=[rule]


    OneRuleFile.run()


    for one_result in OneRuleFile.contains[0].result:
        print(one_result,one_result.criticity)


def AbsoluteOrRelativeCheck_FABRICATION():
    Chemin = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
    file=ifcopenshell.open(Chemin)

    list_of_wall=file.by_type("IFCWALL")[0:10]
    list_of_slab=file.by_type("IFCSLAB")[0:10]


    number_wall=len(list_of_wall)
    number_slab=len(list_of_slab)

    import random

    number_of_result=random.randint(15,30)
    print(number_of_result)


    list_of_result=[]
    

    for x in range(0,number_of_result):
        source_int=random.randint(0,number_wall-1)
        target_int=random.randint(0,number_slab-1)
        
        result=RuleClass.ClashResultTwoObjects(source=list_of_wall[source_int],target=list_of_slab[target_int],state=True)

        list_of_result.append(result)

    AbsOrRel=RuleClass.AbsoluteOrRelativeChecking(type="Absolute_Number")
    AbsOrRel.relative_source_number=1
    AbsOrRel.relative_operation="="
    AbsOrRel.relative_target_number=2

    AbsOrRel.absolute_operation="<"
    AbsOrRel.absolute_number=3
    

    
    AbsOrRel.run(list_of_result)

def test_one_object_rule_grouping():
    Chemin = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
    OneRuleFile = RuleClass.RuleFile()
    OneRuleFile.list_ifc_path= [Chemin]

    Source_Select = SelectFacet()
    Source_Facet = ids.Entity(name="IFCSPACE")
    Source_Select.applicability = [Source_Facet]

    rule=Volume(Source_Select,0.1,1)

    rule.select_grouping="ENTITY"
    rule.select_grouping=ids.Property(propertySet="PSet_Revit_Other",baseName="VentilationZoneName")
    rule.select_grouping=ids.Attribute(name="Name")
    rule.select_grouping=ids.PartOf(name="Name")

    OneRuleFile.contains=[rule]

    OneRuleFile.run()


    for result in rule.grouped_result:
        print(result)

def create_OBB_clash():
    Chemin = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
    OneRuleFile = RuleClass.RuleFile()
    OneRuleFile.list_ifc_path= [Chemin]

    Source_Select = SelectFacet()
    Source_Facet = ids.Entity(name="IFCSLAB")
    Source_Select.applicability = [Source_Facet]


    Source_Select2 = SelectFacet()
    Source_Facet2 = ids.Entity(name="IFCFURNISHINGELEMENT")
    Source_Select2.applicability = [Source_Facet2]

    rule=OBB_Below(Source_Select,Source_Select2,0.6)


    OneRuleFile.contains=[rule]

    OneRuleFile.run()

    for result in rule.result:
        if result.source==result.target:
            continue
        print()
        print(result.source,result.target)

def create_RayCheck_clash():
    Chemin = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
    OneRuleFile = RuleClass.RuleFile()
    OneRuleFile.list_ifc_path= [Chemin]

    Source_Select = SelectFacet()
    Source_Facet = ids.Entity(name="IFCFURNISHINGELEMENT")
    Source_Select.applicability = [Source_Facet]

    Source_Select2 = SelectFacet()
    Source_Facet2 = ids.Entity(name="IFCFURNISHINGELEMENT")
    Source_Select2.applicability = [Source_Facet2]

    Source_Select3 = SelectFacet()
    Source_Facet3 = ids.Entity(name="IFCWALLSTANDARDCASE")
    Source_Select3.applicability = [Source_Facet3]


    rule=Ray_Check(Source_Select,Source_Select2,Source_Select3,100)


    OneRuleFile.contains=[rule]

    OneRuleFile.run()

    for result in rule.result:
        if result.source==result.target:
            continue

def create_display():
    Chemin = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
    OneRuleFile = RuleClass.RuleFile()
    OneRuleFile.list_ifc_path= [Chemin]

    Source_Select = SelectFacet()
    Source_Facet = ids.Entity(name="IfcWindow")
    Source_Select.applicability = [Source_Facet]


    Source_Select2 = SelectFacet()
    Source_Facet2 = ids.Entity(name="IfcSlab")
    Source_Select2.applicability = [Source_Facet2]

    rule=OBB_Below(Source_Select,Source_Select2,0.1)

    OneRuleFile.contains=[rule]
    OneRuleFile.load_file()
    OneRuleFile.update_file_info()


    rule.display()



if __name__ == "__main__":
    create_display()
