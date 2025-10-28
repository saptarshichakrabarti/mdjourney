flowchart TD
 subgraph subGraph0["User Actions"]
        Fm{"On Folder Created?"}
        A["Create Project Folder p_MyProject"]
        B["Create Dataset Folder p_MyProject/Dataset"]
        Gf{"On File Created?"}
        C["Add Data File<br>p_MyProject/Dataset/file.ext"]
        D["Create Contextual Template Trigger File<br>dataset metadata trigger...json"]
        Hf{"On File Modified?"}
        E["Edit/Complete experiment_contextual_XXX.json<br>Manual fill of placeholders"]
  end
 subgraph subGraph1["Monitor folder_monitor.py"]
        Mg_Proj("generate_project_file")
        Mg_Dataset("generate_dataset_files")
        Mg_Contextual_Trigger("create_experiment_contextual_template")
        Fp_ProcessFile("process_file_with_dirmeta")
        Vg_CheckComplete("check_contextual_metadata_completion")
  end
 subgraph Utilities["Utilities"]
        U_Utils["src/utils.py<br>Timestamp and Checksum"]
  end
 subgraph subGraph3["Schema Manager"]
        Sm_LoadValidate["src/schema_manager.py\nLoad and Validate Schemas"]
  end
 subgraph subGraph4["Metadata Generator"]
        Vc_Commit("commit_metadata_changes")
  end
 subgraph subGraph5["File Processor"]
        Ext_Dirmeta["dirmeta Library"]
        Vc_DvcAdd("add_data_file_to_dvc")
  end
 subgraph subGraph6["V2 Generator"]
        Vg_GenerateV2("generate_complete_metadata_file")
  end
 subgraph subGraph7["Version Control"]
        Vc_Manager["src/version_control.py<br>Manager Class"]
  end
 subgraph src["src"]
        Utilities
        subGraph3
        subGraph4
        subGraph5
        subGraph6
        subGraph7
  end
 subgraph subGraph9["External Tools"]
  end
    A --> Fm
    B --> Fm
    C --> Gf
    D --> Gf
    E --> Hf
    Fm -- Yes, p_ prefix Project --> Mg_Proj
    Fm -- Yes, in Project Dataset --> Mg_Dataset
    Gf -- "Yes, trigger_contextual_template_FOR_XXX.json" --> Mg_Contextual_Trigger
    Gf -- Yes, Data File not metadata --> Fp_ProcessFile
    Hf -- "Yes, experiment_contextual_XXX.json" --> Vg_CheckComplete
    Sm_LoadValidate --- U_Utils
    Mg_Proj --> Sm_LoadValidate & U_Utils & Vc_Commit
    Mg_Dataset --> Sm_LoadValidate & U_Utils & Vc_Commit
    Mg_Contextual_Trigger --> Sm_LoadValidate & U_Utils & Vc_Commit
    Fp_ProcessFile --> Sm_LoadValidate & U_Utils & Vc_Commit & Vc_DvcAdd
    Fp_ProcessFile -- Calls dirmeta External --> Ext_Dirmeta
    Vg_CheckComplete --> Sm_LoadValidate & U_Utils
    Vg_CheckComplete -- If complete --> Vg_GenerateV2
    Vg_GenerateV2 --> Sm_LoadValidate & U_Utils & Vc_Commit
    Vc_Manager --> Vc_Commit & Vc_DvcAdd
    Fm --- Mg_Proj & Mg_Dataset
    Gf --- Mg_Contextual_Trigger & Fp_ProcessFile
    Hf --- Vg_CheckComplete

     Fm:::monitor_orchestrator
     A:::user_action
     B:::user_action
     Gf:::monitor_orchestrator
     C:::user_action
     D:::user_action
     Hf:::monitor_orchestrator
     E:::user_action
     Mg_Proj:::src_module
     Mg_Dataset:::src_module
     Mg_Contextual_Trigger:::src_module
     Fp_ProcessFile:::src_module
     Vg_CheckComplete:::src_module
     U_Utils:::src_module
     Sm_LoadValidate:::src_module
     Vc_Commit:::src_module
     Ext_Dirmeta:::external_tool
     Vc_DvcAdd:::src_module
     Vg_GenerateV2:::src_module
     Vc_Manager:::src_module
    classDef user_action fill:#e0f7fa,stroke:#0097a7,stroke-width:2px,color:#000
    classDef monitor_orchestrator fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#000
    classDef src_module fill:#e8f5e9,stroke:#4caf50,stroke-width:2px,color:#000
    classDef external_tool fill:#f5f5f5,stroke:#bdbdbd,stroke-width:1px,color:#000
    style Vc_Commit fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px,color:#000
    style Vc_DvcAdd fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px,color:#000
    style Vc_Manager fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px,color:#000
