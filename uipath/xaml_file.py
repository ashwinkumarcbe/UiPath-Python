import os
from bs4 import BeautifulSoup

class Class:
	def __init__(self, file):
		self.file = file

		#throw error if file doesnt exist, else load it
		if os.path.isfile(file):
			self.xaml = self.read_xaml()
		else:
			raise("File not found. Cannot load class.")

#Getters and Setters:------------------------------------------------------------------------------------------------------------------


	#Gets the existing XAML
	def get_xaml(self):
		return self.xaml

	#Gets the name
	def get_name(self):
		return self.xaml.find("Activity")["x:Class"]

	#Sets the name/updates the name
	def set_name(self, name):
		return self.update_xaml_item(self.xaml.find("Activity"), name, "x:Class")

	#Returns the ID of the sequnce, not sure if this is even ever used
	def get_id(self):
		#check if the ID is in the activity tag, if it isn't we will return the actual tag. This happens on main classes.
		in_activity = ("sap2010:WorkflowViewState.IdRef" in self.xaml.find("Activity"))
		#If it wasn't found, we will return the first occurance of the ID tag
		if in_activity is False:
			return self.xaml.find("sap2010:WorkflowViewState.IdRef").string
		else:
			return self.xaml.find("Activity")["sap2010:WorkflowViewState.IdRef"]

	#Sets a sequence ID. Again, not sure if this is ever used or if this is even a good idea
	def set_id(self, new_id):
		#check if the ID is in the activity tag, if it isn't we will upate the actual tag. This happens on main classes.
		in_activity = ("sap2010:WorkflowViewState.IdRef" in self.xaml.find("Activity"))
		#If it wasn't found, we will change the first occurance of the ID tag
		if in_activity is False:
			return self.update_xaml_item(self.xaml.find("sap2010:WorkflowViewState.IdRef"), new_id)
		else:
			return self.update_xaml_item(self.xaml.find("Activity"), name, "sap2010:WorkflowViewState.IdRef")

	#Gets the "main" sequence that contains all actvities in the class
	def get_main_activity(self):
		return Class.Activity(self, self.xaml.find("TextExpression.ReferencesForImplementation").next_sibling.next_sibling)

	#Get all activitiies
	def get_activities(self):
		activities = []
		self.xaml.find("TextExpression.ReferencesForImplementation").find_all()

	#Gets all arguments for the class
	def get_arguments(self):
		arguments = []
		for item in self.xaml.find_all("x:Property"):
			arguments.append(Class.Argument(self,item))
		return arguments

	#Gets argument by name
	def get_argument_by_name(self, name):
		xaml=self.xaml.find("x:Property", Name=name)
		if xaml is None or xaml == "None":
			raise Exception("Argument with name: {} could not be found.".format(name))
		else:
			return Class.Argument(self, xaml=self.xaml.find("x:Property", Name=name))

#Helper functions:----------------------------------------------------------------------------------------------------------------------

	#Updates any item passed into it
	def update_xaml_item(self, item, new_value, attr=None):
		#If attr = None then we just assign the string ("inner_html") to whatever the new value is
		if attr is None:
			item.string = new_value
			to_return = item.string
		else:
			item[attr] = new_value
			to_return = item[attr]
		self.save()
		return to_return

	#Saves the raw XAML in memory to the XAML file in storage
	def save(self):
		#First we need to strip the <XML> tag that our xaml parser adds
		#xml_string = '<?xml version="1.0" encoding="utf-8"?>\n' # The XML encoding tag we need to remove
		#data = str(self.xaml).replace(xml_string, "", 1)

		file = open(self.file,"w+")
		file.write(self.xaml.prettify())
		file.close()

		#return file

	#Reads an XAML file
	def read_xaml(self):
		infile = open(self.file, "r")
		data = infile.read()
		infile.close()

		data = data[data.find("<"):len(data)] # remove garbage from start of file
		xaml = BeautifulSoup(data, "xml");
		print(xaml.find_all(True, version="1.0"))
		return xaml

	#To String.
	def __str__(self):
		return self.get_name()


	#-----------------------------------------------------------------------------------------------------------------------
	#  Subclass: Argument
	#  Description: Methods for manipulating and creating arguments for sequences/classes
	#-----------------------------------------------------------------------------------------------------------------------

	#Define subclass for the arguments
	class Argument():
		def __init__(self, parent, xaml=None, name=None, arg_type=None, data_type=None, default_value=None, default_value_is_variable=None):
			self.xaml = xaml
			self.parent = parent

			#If user doesn't provide XAML or Name, set self to None so we don't create empty Arguments
			if self.xaml is None and name is None:
				self = None
			else:
				#If the user doesn't pass in a XAML or BS node, we will build a new argument
				if self.xaml is None and not name is None:

					#Check if argument with same name already exists
					if self.parent.xaml.find("x:Property", Name=name):
						 raise Exception("Argument with the name: {} already exists. Cannot create another.".format(name))
					#If it does not exist, create the new argument
					else:
						self.xaml = self.parent.xaml.new_tag("x:Property")
						self.xaml['Name'] = name

						#Build the Type="InArgument(x:String)" property for the appropriate arg type
						if arg_type == "Property" or arg_type is None:
							self.xaml["Type"] = data_type
						else:
							self.xaml["Type"] = arg_type + "(" + data_type + ")"

						#check for x:Members, if this doesn't exist, we will have to create it before appending the new argument
						if self.parent.xaml.find("x:Members") is None:
							self.parent.xaml.find("Activity").insert(0, self.parent.xaml.new_tag("x:Members"))
						
						#Add the newly created tag
						self.parent.xaml.find("Activity").find("x:Members").append(self.xaml)

						#Set the default value if one was passd in
						if not default_value is None and arg_type != "OutArgument":
							self.set_default_value(default_value, default_value_is_variable)

						#Save the parent Class
						self.parent.save()

		#Returns name of argument
		def get_name(self):
			return self.xaml["Name"]

		#Updates the name of the argument
		def set_name(self, new_name):
			#Check for default value and change the name there too
			temp = self.get_default_value()
			if not temp is None:
				del self.parent.xaml.find("Activity")["this:" + self.parent.get_name() + "." + self.get_name()]
				self.parent.xaml.find("Activity")["this:" + self.parent.get_name() + "." + new_name] = temp

			self.xaml["Name"] = new_name
			self.parent.save()

			return self.xaml["Name"]

		#Gets the data_type
		def get_data_type(self):
			if "(" in self.xaml["Type"]:
				return self.xaml["Type"].split("(", 2)[1][0:len(self.xaml["Type"].split("(", 2)[1])-1]
			else:
				return self.xaml["Type"]

		#Sets the datatype
		def set_data_type(self, new_data_type):
			if "(" in self.xaml["Type"]:
				self.xaml["Type"] = self.get_arg_type() + "(" + new_data_type + ")"
			else:
				self.xaml["Type"] = new_data_type
			self.parent.save()
			return self.xaml["Type"]

		#Gets the arg_type
		def get_arg_type(self):
			if "(" in self.xaml["Type"]:
				return self.xaml["Type"].split("(", 1)[0]
			else:
				return "Property"

		#Set a new arg type
		def set_arg_type(self, new_arg_type):
			if new_arg_type == "Property":
				self.xaml["Type"] = self.get_data_type()
			else:
				self.xaml["Type"] = new_arg_type + "(" + self.get_data_type() + ")"

			#If new arg type is OutArgument and there is an existing out argument, delete the default value
			if new_arg_type == "OutArgument" and self.get_default_value != None:
				del self.parent.xaml.find("Activity")["this:" + self.parent.get_name() + "." + self.get_name()]

			self.parent.save()
			return self.xaml["Type"]

		#Gets the default value
		def get_default_value(self):
			if ("this:" + self.parent.get_name() + "." + self.get_name()) in self.parent.xaml.find("Activity").attrs:
				return self.parent.xaml.find("Activity")["this:" + self.parent.get_name() + "." + self.get_name()]

		#Sets the default value
		def set_default_value(self, new_default_value, is_variable=None):			
			#For UiPath to properly read non-string values from the XAML, we have to surround it with square brackets. Same with variables.
			if is_variable == True or self.get_data_type != "x:String":
				new_default_value = "[" + new_default_value + "]" #BUG, possible bug if there is a string variable set to default

			#Throw error if argument is an OutArgument because they can't have default values
			if self.get_arg_type() != "OutArgument":
				self.parent.xaml.find("Activity")["this:" + self.parent.get_name() + "." + self.get_name()] = new_default_value

				self.parent.save()
			else:
				#If there is somehow already a default value, delete it
				if self.get_default_value != None:
					del self.parent.xaml.find("Activity")["this:" + self.parent.get_name() + "." + self.get_name()]
				raise Exception("Cannot set default value of argument: {} because it is an OutArgument".format(self.get_name()))
			
			return self.parent.xaml.find("Activity")["this:" + self.parent.get_name() + "." + self.get_name()]

	#-----------------------------------------------------------------------------------------------------------------------
	#  Subclass: Activity
	#  Description: Methods for manipulating and creating activities inside of classes/sequences
	#-----------------------------------------------------------------------------------------------------------------------

	#Define subclass for the arguments
	class Activity():
		def __init__(self, parent, xaml=None, type=None, name=None, id=None, annotation=None, attributes=None, variables=None, contents=None):
			self.parent = parent
			self.xaml = xaml

			if self.xaml is None:
				pass #STUB

		#Gets name of the activity
		def get_name(self):
			if "DisplayName" in self.xaml.attrs:
				return self.xaml["DisplayName"]
			else:
				return ""

		#Sets the name of the activity
		def set_name(self, new_name):
			self.xaml["DisplayName"] = new_name
			self.parent.save()
			return self.xaml["DisplayName"]

		#Gets the activity type. For example, sequence/assign/try/catch, etc...
		def get_type(self):
			return self.xaml.name

		#Notice there is no setter for type for this subclass. Instead just delete the activity and create a new one in its place.

		#Gets all attributes of the activity
		def get_attributes(self):
			return self.xaml.attrs

		#Gets the value of the passed in attribute
		def get_attribute_value(self, attribute):
			return self.xaml[attribute]

		#Sets attribute value
		def set_attribute_value(self, attribute, new_value):
			self.xaml[attribute] = new_value
			self.parent.save()
			return self.xaml[attribute]

		#Gets the value of the bs tag
		def get_value(self):
			if self.xaml.string is None:
				return ""
			else:
				return self.xaml.string

		#Gets the ID of the activity
		def get_id(self):
			return self.xaml["sap2010:WorkflowViewState.IdRef"]

		#Sets ID of activity
		def set_id(self, new_id):
			self.xaml["sap2010:WorkflowViewState.IdRef"] = new_id
			self.parent.save()
			return self.xaml["sap2010:WorkflowViewState.IdRef"]

		#Gets the annotation
		def get_annotation(self):
			return self.xaml["sap2010:Annotation.AnnotationText"]

		#Sets the annotation
		def set_annotation(self, new_annotation):
			self.xaml["sap2010:Annotation.AnnotationText"] = new_annotation
			self.parent.save()
			return self.xaml["sap2010:Annotation.AnnotationText"]

		#Gets xaml contents of activity
		def get_contents(self):
			contents = []
			for item in self.xaml.find_all(True, recursive=False):
				contents.append(Class.Activity(self, item))

			return contents

		#Appends a new activity to a sequence/try catch/etc
		def append(self, tag):
			self.xaml.append(tag)
			self.parent.save()
			return self.xaml

		#Returns list of all variables in this sequence
		def get_variables(self):
			variables = []
			for item in self.xaml.find(self.get_type() + ".Variables").contents:
				variables.append(Class.Activity.Variable(self,item))
			return variables

		#Gets argument by name
		def get_variable_by_name(self, name):
			return Class.Activity.Variable(self, xaml=self.xaml.find(self.get_type() + ".Variables").contents.find("Variable", Name=name))

		#-----------------------------------------------------------------------------------------------------------------------
		#  Subclass: Variable
		#  Description: Methods for manipulating and creating variables of activities
		#-----------------------------------------------------------------------------------------------------------------------

		class Variable:
			def __init__(self, parent, xaml=None, name=None, variable_type=None, default_value=None):
				self.parent = parent
				self.xaml = xaml

				#IF no XAML was passed we need to create a new tag based on the parameters
				if xaml is None:
					#check to see if the parent activity has a ActivityName.Variables tag that we can add this to
					#if it doesnt we will have to create it
					if self.parent.xaml.find(self.parent.get_type() + ".Variable") is None:
						self.parent.xaml.insert(self.parent.parent.xaml.new_tag(self.parent.get_type() + ".Variables"), 0)

					#Build the new variable
					new_tag = self.parent.parent.xaml.new_tag("Variable")
					new_tag["Name"] = name
					new_tag["x:TypeArguments"] = variable_type

					if not default_value is None:
						new_tag["Default"] = default_value



					self.parent.parent.save() #Save the main .xaml file now

			#Gets the name
			def get_name(self):
				return self.xaml["Name"]

			#Sets the name
			def set_name(self, new_name):
				self.xaml["Name"] = new_name
				self.parent.save()
				return self.xaml["Name"]

			#Gets the datatype
			def get_data_type(self):
				return self.xaml["x:TypeArguments"]

			#Sets the datatype
			def set_data_type(self, new_data_type):
				self.xaml["x:TypeArguments"] = new_data_type
				self.parent.parent.save()
				return self.xaml["x:TypeArguments"]

			#Gets the default value
			def get_default_value(self):
				return self.xaml["Default"]

			#Sets the default value
			def set_default_value(self, new_default_value):
				self.xaml["Default"] = new_default_value
				self.parent.parent.save()
				return self.xaml["Default"]