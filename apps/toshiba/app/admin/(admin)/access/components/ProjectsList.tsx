import {
  CommonModal,
  ElevaiteIcons,
  type CommonMenuItem,
} from "@repo/ui/components";
import { useEffect, useState } from "react";
import { ListHeader } from "../../lib/components/ListHeader";
import {
  ListRow,
  specialHandlingListRowFields,
  type RowStructure,
} from "../../lib/components/ListRow";
import { useRoles } from "../../lib/contexts/RolesContext";
import {
  type ExtendedProjectObject,
  type ProjectObject,
  type SortingObject,
} from "../../lib/interfaces";
import { AddEditProject } from "./Add Edit Modals/AddEditProject";
import "./ProjectsList.scss";

enum menuActions {
  EDIT = "Edit",
}

interface ProjectsListProps {
  isVisible: boolean;
}

export function ProjectsList(props: ProjectsListProps): JSX.Element {
  const rolesContext = useRoles();
  const [displayProjects, setDisplayProjects] = useState<
    ExtendedProjectObject[]
  >([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [sorting, setSorting] = useState<SortingObject<ExtendedProjectObject>>({
    field: undefined,
  });
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<
    ExtendedProjectObject | undefined
  >();

  const projectsListStructure: RowStructure<ExtendedProjectObject>[] = [
    { header: "Project Name", field: "name", isSortable: true },
    { header: "Account", field: "accountName", isSortable: true },
    { header: "Parent Project", field: "parentProjectName", isSortable: true },
    {
      header: "Creator",
      field: "creator",
      isSortable: true,
      specialHandling: specialHandlingListRowFields.EMAIL,
    },
    { header: "Description", field: "description", isSortable: false },
  ];

  const projectsListMenu: CommonMenuItem<ExtendedProjectObject>[] = [
    {
      label: "Edit Project",
      onClick: (item: ExtendedProjectObject) => {
        handleMenuClick(item, menuActions.EDIT);
      },
    },
  ];

  useEffect(() => {
    arrangeDisplayProjects();
  }, [rolesContext.projects, searchTerm, sorting]);

  function arrangeDisplayProjects(): void {
    const expandedProjects = getProjectsWithProjectDetails(
      rolesContext.projects
    );

    // Search
    const searchedList: ExtendedProjectObject[] = searchTerm
      ? []
      : expandedProjects;
    if (searchTerm) {
      for (const item of expandedProjects) {
        if (item.name.toLowerCase().includes(searchTerm.toLowerCase())) {
          searchedList.push(item);
          continue;
        }
        if (
          item.accountName?.toLowerCase().includes(searchTerm.toLowerCase())
        ) {
          searchedList.push(item);
          continue;
        }
        if (
          item.parentProjectName
            ?.toLowerCase()
            .includes(searchTerm.toLowerCase())
        ) {
          searchedList.push(item);
          continue;
        }
        if (item.creator?.toLowerCase().includes(searchTerm.toLowerCase())) {
          searchedList.push(item);
          continue;
        }
        // Add other checks here as desired.
      }
    }

    // Sort
    const sortedList: ExtendedProjectObject[] = searchedList;
    if (sorting.field) {
      sortedList.sort((a, b) => {
        if (
          sorting.field &&
          typeof a[sorting.field] === "string" &&
          typeof b[sorting.field] === "string" &&
          !Array.isArray(a[sorting.field]) &&
          !Array.isArray(b[sorting.field])
        )
          return (a[sorting.field] as string).localeCompare(
            b[sorting.field] as string
          );
        return 0;
      });
      if (sorting.isDesc) {
        sortedList.reverse();
      }
    }

    // Set
    setDisplayProjects(sortedList);
  }

  function handleAddProject(): void {
    setIsModalOpen(true);
  }

  function handleEditProject(project: ExtendedProjectObject): void {
    setSelectedProject(project);
    setIsModalOpen(true);
  }

  function handleModalClose(): void {
    setSelectedProject(undefined);
    setIsModalOpen(false);
  }

  function handleSearch(term: string): void {
    if (!props.isVisible) return;
    setSearchTerm(term);
  }

  function handleSort(field: keyof ExtendedProjectObject): void {
    let sortingResult: SortingObject<ExtendedProjectObject> = {};
    if (sorting.field !== field) sortingResult = { field };
    if (sorting.field === field) {
      if (sorting.isDesc) sortingResult = { field: undefined };
      else sortingResult = { field, isDesc: true };
    }
    setSorting(sortingResult);
  }

  function handleMenuClick(
    project: ExtendedProjectObject,
    action: menuActions
  ): void {
    switch (action) {
      case menuActions.EDIT:
        handleEditProject(project);
        break;
      default:
        break;
    }
  }

  function getProjectsWithProjectDetails(
    projects: ProjectObject[]
  ): ExtendedProjectObject[] {
    const formattedProjects = JSON.parse(
      JSON.stringify(projects)
    ) as ExtendedProjectObject[];

    for (const project of formattedProjects) {
      // Add account name
      if (project.account_id) {
        const foundAccount = rolesContext.accounts?.find(
          (item) => item.id === project.account_id
        );
        if (foundAccount) {
          project.accountName = foundAccount.name;
        }
      }
      // Add Parent Project name
      if (project.parent_project_id) {
        const foundParentProject = rolesContext.projects.find(
          (item) => item.id === project.parent_project_id
        );
        if (foundParentProject) {
          project.parentProjectName = foundParentProject.name;
        }
      }
    }

    return formattedProjects;
  }

  return (
    <div className="projects-list-container">
      <ListHeader
        label="Projects List"
        addLabel="Add Project"
        addIcon={<ElevaiteIcons.SVGCross />}
        addAction={handleAddProject}
        onSearch={handleSearch}
        searchPlaceholder="Search Projects"
        isVisible={props.isVisible}
      />

      <div className="accounts-list-table-container">
        <ListRow<ExtendedProjectObject>
          isHeader
          structure={projectsListStructure}
          menu={projectsListMenu}
          onSort={handleSort}
          sorting={sorting}
        />
        {displayProjects.length === 0 && rolesContext.loading.accounts ? (
          <div className="table-span empty">
            <ElevaiteIcons.SVGSpinner />
            <span>Loading...</span>
          </div>
        ) : displayProjects.length === 0 ? (
          <div className="table-span empty">
            There are no projects to display.
          </div>
        ) : (
          displayProjects.map((project, index) => (
            <ListRow<ExtendedProjectObject>
              key={project.id}
              rowItem={project}
              structure={projectsListStructure}
              menu={projectsListMenu}
              menuToTop={
                displayProjects.length > 4 && index > displayProjects.length - 4
              }
            />
          ))
        )}
      </div>

      {!isModalOpen ? null : (
        <CommonModal onClose={handleModalClose}>
          <AddEditProject
            project={selectedProject}
            onClose={handleModalClose}
          />
        </CommonModal>
      )}
    </div>
  );
}
