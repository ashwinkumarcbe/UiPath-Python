import glob
from .functions import Functions
from .sequence import Sequence

import os

class_default_xaml = '<Activity x:Class="Main" mva:VisualBasic.Settings="Assembly references and imported namespaces for internal implementation" xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities" xmlns:mv="clr-namespace:Microsoft.VisualBasic;assembly=Microsoft.VisualBasic" xmlns:mva="clr-namespace:Microsoft.VisualBasic.Activities;assembly=System.Activities" xmlns:s="clr-namespace:System;assembly=mscorlib" xmlns:sc="clr-namespace:System.Collections;assembly=mscorlib" xmlns:scg="clr-namespace:System.Collections.Generic;assembly=mscorlib" xmlns:sd="clr-namespace:System.Data;assembly=System.Data" xmlns:sd1="clr-namespace:System.Diagnostics;assembly=System" xmlns:sd2="clr-namespace:System.Drawing;assembly=System.Drawing" xmlns:si="clr-namespace:System.IO;assembly=mscorlib" xmlns:sl="clr-namespace:System.Linq;assembly=System.Core" xmlns:snm="clr-namespace:System.Net.Mail;assembly=System" xmlns:sx="clr-namespace:System.Xml;assembly=System.Xml" xmlns:sxl="clr-namespace:System.Xml.Linq;assembly=System.Xml.Linq" xmlns:uc="clr-namespace:UiPath.Core;assembly=UiPath.Core" xmlns:uca="clr-namespace:UiPath.Core.Activities;assembly=UiPath.Core.Activities" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" />'
project_default_json = Functions.get_json_from_string('{"name":"","description":"","main":"Main.xaml","dependencies":{"UiPath.UIAutomation.Activities":"[19.2.0]","UiPath.System.Activities":"[19.2.0]","UiPath.Excel.Activities":"[2.5.2]","UiPath.Mail.Activities":"[1.3.0]"},"schemaVersion":"3.2","studioVersion":"19.2.0.0","projectVersion":"1.0.0","runtimeOptions":{"autoDispose":false,"excludedLoggedData":["Private:*","*password*"]},"projectType":"Workflow","libraryOptions":{"includeOriginalXaml":false,"privateWorkflows":[]}}')

class Project:
	def __init__(self, path=None, name=None, description=None, main_class_name=None):
		self.path = path
		self.name = name
		self.description = description
		self.json = ""
		self.main_class = ""

		#If a user passed a name, they want to create a new project.
		#If they didn't they want to load an existing one.
		if name is None:
			#Load project
			self.load_existing()
		else:
			#Create new project
			self.create_new(main_class_name)

	#Creates a new project from the project path
	def create_new(self, main_class_name=None):
		#Create the main directory if it does not already exist. Also creates the parent dirs
		Functions.create_dir(self.path)
		#Create the hidden folders that a project contains, just for development sake
		Functions.create_dir(os.path.join(self.path, ".screenshots"))
		Functions.create_dir(os.path.join(self.path, ".local"))

		#Edit project.json and save
		project_json = project_default_json
		project_json["name"] = self.name
		project_json["description"] = self.description

		class_name = "Main"
		
		#If a user supplied a main class name, we will use that instead of "Main" and "Main.xaml"
		if not main_class_name is None:
			class_name = main_class_name
		#Update main json 
		project_json["main"] = class_name + ".xaml"

		#Update self.main_class
		self.main_class = class_name

		#Replace classname in XAML string
		main_xaml = class_default_xaml.replace('x:Class="Main"', 'x:Class="' + class_name + '"')
		#Create XAML file for the main sequence
		Functions.create_file(os.path.join(self.path, class_name + ".xaml"), main_xaml)

		#Create project.json
		Functions.update_json(os.path.join(self.path, "project.json"), project_json)
		

	#Loads an existing project
	def load_existing(self):
		self.json = Functions.read_json(os.path.join(self.path, "project.json"))
		self.name = self.json["name"]
		self.description = self.json["description"]
		self.main_class = self.json["main"]

	#Gets all sequences in this project
	def get_all_classes(self):
		return list(map(self.get_relative_path, glob.glob(os.path.join(self.path, "**", "*" + ".xaml"), recursive=True)))

	#Removes the absolute path for a sequence and returns the relative path
	def get_relative_path(self, file):
		return file[len(self.path)+1:len(file)]

	#Load a class/sequence. Input is relative path to the sequence
	def load_class(self, sequence):
		return Sequence(os.path.join(self.path, sequence))

	#Creats a new class/sequence
	#like this: rel_path="new_directory_in_project" name="TestSequence"
	# results in ProjectRootDir\new_directory_in_project\TestSequence.xaml
	def create_class(self, rel_path, name):
		xaml = class_default_xaml.replace('x:Class="Main"', 'x:Class="' + name + '"')
		#Create any parent dirs that need to be created
		Functions.create_dir(os.path.join(self.path, rel_path))
		#Create XAML file for the main sequence
		Functions.create_file(os.path.join(self.path, rel_path, name + ".xaml"), xaml)

		#Create a new sequence class by opening the newly created file
		return Sequence(os.path.join(self.path, rel_path, name + ".xaml"))
